#!/usr/bin/env python3
"""
ping_mesh.py - rent small servers in many cities, ping every one from every
other, collect the results, and delete everything again.

Each server runs verified_ping.py (kernel timestamps at the sender,
hash-checked payloads) against every other server. The result is a full
table of minimum round-trip times between known datacentres.

    python3 ping_mesh.py up            # create the servers (asks first, shows cost)
    python3 ping_mesh.py status        # list what is running
    python3 ping_mesh.py run           # every server pings every other -> mesh_pings.csv
    python3 ping_mesh.py collect       # fetch results already finished on the servers (no re-ping)
    python3 ping_mesh.py compare       # Vultr vs AWS, city pair by city pair -> mesh_compare.csv
    python3 ping_mesh.py down          # delete every server and helper this script made

    python3 ping_mesh.py up --vultr-only    or    --aws-only

Run from the folder that holds verified_ping.py.

Needs
  Vultr: environment variable VULTR_API_KEY (Vultr: Account > API). Add your
         public IP to the API access list there, or the API refuses.
  AWS:   (Santiago runs in an AWS Local Zone off us-east-1; the script opts in and
         makes its subnet itself.)
         pip install boto3, and credentials from `aws configure` (or the usual
         AWS environment variables). Opt-in regions (Melbourne, Auckland,
         Cape Town) must be enabled once in the AWS console under
         Account > AWS Regions; the script skips any that are not.
  SSH:   a key pair, by default ~/.ssh/id_ed25519(.pub). Override with --key.

Files written next to this script (names chosen not to clash with others):
  mesh_servers.json   what was created (used by status, run and down)
  mesh_known_hosts    SSH host keys for these servers only
  mesh_raw/           each server's raw verified_ping CSVs
  mesh_pings.csv      the combined table: one row per (from, to) pair
  mesh_compare.csv    the same city pairs measured on Vultr and on AWS, side by side

Everything created is labelled/tagged "fibre-mesh". `down` deletes by that
tag as well as by the manifest, so nothing is left running by accident.
Servers bill by the hour until deleted: run `down` when finished.
Python 3 stdlib, plus boto3 for AWS.
"""
import argparse, base64, csv, json, math, os, statistics, subprocess, sys, tarfile, threading, time
import unicodedata, urllib.error, urllib.request

TAG = "fibre-mesh"
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "mesh_servers.json")
KNOWN = os.path.join(HERE, "mesh_known_hosts")
RAW = os.path.join(HERE, "mesh_raw")
OUT = os.path.join(HERE, "mesh_pings.csv")
CMP = os.path.join(HERE, "mesh_compare.csv")
C_KM_S = 299_792.458
R_EARTH = 6371.0088

# ---------------- configuration: edit these lists to change the mesh ----------------
# Vultr: matched against Vultr's own region list by city name.
VULTR_CITIES = ["Seattle", "Silicon Valley", "Los Angeles", "Honolulu", "Miami", "New Jersey",
                "London", "Amsterdam", "Stockholm", "Tokyo", "Osaka", "Seoul", "Singapore",
                "Sydney", "Melbourne", "Mumbai", "Sao Paulo", "Johannesburg"]
# Vultr Santiago left out: it would not finish provisioning (12-13 Nov 2026).
# Santiago comes from AWS instead (Local Zone, below).
# AWS: region code -> city. The first ten match Vultr cities, so every city pair
# among them is measured twice, on two independent networks (the double check).
# The last two add southern places Vultr lacks. Opt-in regions are marked.
AWS_REGIONS = {
    "eu-west-2":      "London",
    "eu-north-1":     "Stockholm",
    "ap-northeast-1": "Tokyo",
    "ap-northeast-3": "Osaka",
    "ap-northeast-2": "Seoul",
    "ap-southeast-1": "Singapore",
    "ap-southeast-2": "Sydney",
    "ap-southeast-4": "Melbourne",     # opt-in
    "ap-south-1":     "Mumbai",
    "sa-east-1":      "Sao Paulo",
    "ap-southeast-6": "Auckland",      # opt-in, AWS only
    "af-south-1":     "Cape Town",     # opt-in, AWS only
    # add the AWS Chile region code here once it has launched
}
# AWS Local Zones: small AWS sites in cities without a full region. They hang off
# a parent region, need a one-time opt-in, their own subnet, gp2 disks and a
# limited set of instance types; the script handles all of that.
AWS_LOCAL_ZONES = {
    "Santiago": {"region": "us-east-1", "zone": "us-east-1-scl-1a", "group": "us-east-1-scl-1",
                 "cidr": "172.31.240.0/24"},
}
AWS_INSTANCE_TYPE = "t3.micro"
LZ_TYPES = ["t3.micro", "t3.small", "t3.medium", "c5.large", "m5.large"]
# Datacentre city coordinates (city level, for the analysis).
COORDS = {
    "Seattle": (47.61, -122.33), "Silicon Valley": (37.35, -121.95), "Los Angeles": (34.05, -118.24),
    "Honolulu": (21.31, -157.86), "Miami": (25.76, -80.19), "New Jersey": (40.55, -74.46),
    "London": (51.51, -0.13), "Amsterdam": (52.37, 4.90), "Stockholm": (59.33, 18.07),
    "Tokyo": (35.68, 139.69), "Osaka": (34.69, 135.50), "Seoul": (37.57, 126.98),
    "Singapore": (1.35, 103.82), "Sydney": (-33.87, 151.21), "Melbourne": (-37.81, 144.96),
    "Mumbai": (19.08, 72.88), "Sao Paulo": (-23.55, -46.63), "Santiago": (-33.45, -70.67),
    "Johannesburg": (-26.20, 28.05), "Auckland": (-36.85, 174.76), "Cape Town": (-33.92, 18.42),
    "Jakarta": (-6.21, 106.85),
}
PING_COUNT = 30      # echoes per peer
PING_GAP = 0.2       # mean seconds between echoes (jittered by verified_ping)
CITY_FILTER = []     # set by --cities
# --------------------------------------------------------------------------------------


def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as fh:
            return json.load(fh)
    return {"servers": [], "vultr_ssh_key": None, "aws": {}}


def save_manifest(m):
    with open(MANIFEST, "w") as fh:
        json.dump(m, fh, indent=1)


# ---------------- Vultr (REST API v2, stdlib) ----------------
VAPI = "https://api.vultr.com/v2"

def vultr(method, path, body=None):
    key = os.environ.get("VULTR_API_KEY")
    if not key:
        sys.exit("VULTR_API_KEY is not set")
    req = urllib.request.Request(VAPI + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 4:
                time.sleep(2 + 2 * attempt)
                continue
            detail = e.read().decode(errors="ignore")
            raise RuntimeError(f"Vultr {method} {path}: HTTP {e.code} {detail}") from None


def vultr_up(m, pubkey):
    regions = vultr("GET", "/regions?per_page=500")["regions"]
    by_city = {norm(r["city"]): r for r in regions}
    oses = vultr("GET", "/os?per_page=500")["os"]
    os_id = next((o["id"] for o in oses if o["name"].startswith("Ubuntu 24.04") and "x64" in o["name"]), None)
    if os_id is None:
        sys.exit("Vultr: Ubuntu 24.04 x64 image not found")
    plans = vultr("GET", "/plans?type=all&per_page=500")["plans"]
    # Ubuntu 24.04 needs >= 1 GB; skip IPv6-only and GPU plans.
    plans = [p for p in plans if p.get("ram", 0) >= 1000 and "v6" not in p["id"]
             and not p["id"].startswith("vcg") and "gpu" not in p.get("type", "")]
    if not m.get("vultr_ssh_key"):
        k = vultr("POST", "/ssh-keys", {"name": TAG, "ssh_key": pubkey})["ssh_key"]
        m["vultr_ssh_key"] = k["id"]
        save_manifest(m)
    have = {s["name"] for s in m["servers"]}
    for city in (CITY_FILTER or VULTR_CITIES):
        name = f"vultr-{norm(city).replace(' ', '-')}"
        if name in have:
            continue
        r = by_city.get(norm(city))
        if not r:
            print(f"  Vultr has no region named {city!r}; skipped")
            continue
        avail = [p for p in plans if r["id"] in p.get("locations", [])]
        if not avail:
            print(f"  Vultr {city}: no plan available; skipped")
            continue
        inst, plan = None, None
        for plan in sorted(avail, key=lambda p: p["monthly_cost"])[:4]:
            try:
                inst = vultr("POST", "/instances", {
                    "region": r["id"], "plan": plan["id"], "os_id": os_id, "label": name, "hostname": name,
                    "sshkey_id": [m["vultr_ssh_key"]], "tags": [TAG], "backups": "disabled", "enable_ipv6": False,
                })["instance"]
                break
            except RuntimeError as e:
                print(f"  Vultr {city}: plan {plan['id']} refused ({str(e)[:120]}); trying next")
        if inst is None:
            print(f"  Vultr {city}: could not create a server; skipped")
            continue
        m["servers"].append({"name": name, "provider": "vultr", "city": city, "region": r["id"],
                             "id": inst["id"], "user": "root", "ip": None, "plan": plan["id"],
                             "hourly_usd": round(plan["monthly_cost"] / 672, 4)})
        save_manifest(m)
        print(f"  Vultr {city:15s} {r['id']:5s} {plan['id']}  creating")


def vultr_wait(m):
    for s in m["servers"]:
        if s["provider"] != "vultr" or s.get("ip"):
            continue
        for _ in range(120):
            try:
                i = vultr("GET", f"/instances/{s['id']}")["instance"]
            except RuntimeError as e:
                if "HTTP 404" in str(e):
                    print(f"  Vultr {s['city']}: server no longer exists; dropped from the list (run `up` again to recreate)")
                    s["gone"] = True
                    break
                raise
            if i["status"] == "active" and i["power_status"] == "running" and i["main_ip"] not in ("", "0.0.0.0"):
                s["ip"] = i["main_ip"]
                save_manifest(m)
                print(f"  Vultr {s['city']:15s} {s['ip']}")
                break
            time.sleep(5)


def vultr_down(m):
    ids = {s["id"] for s in m["servers"] if s["provider"] == "vultr"}
    try:
        for i in vultr("GET", f"/instances?tag={TAG}&per_page=500")["instances"]:
            ids.add(i["id"])
    except RuntimeError as e:
        print(f"  could not list Vultr instances by tag: {e}")
    for i in ids:
        try:
            vultr("DELETE", f"/instances/{i}")
            print(f"  Vultr instance {i} deleted")
        except RuntimeError as e:
            print(f"  Vultr instance {i}: {e}")
    if m.get("vultr_ssh_key"):
        try:
            vultr("DELETE", f"/ssh-keys/{m['vultr_ssh_key']}")
        except RuntimeError:
            pass
        m["vultr_ssh_key"] = None
    m["servers"] = [s for s in m["servers"] if s["provider"] != "vultr"]


# ---------------- AWS (boto3) ----------------
def boto():
    try:
        import boto3
        return boto3
    except ImportError:
        sys.exit("AWS needs boto3: pip install boto3   (or use --vultr-only)")


def aws_enabled_regions(b3):
    regs = b3.client("ec2", region_name="us-east-1").describe_regions(AllRegions=True)["Regions"]
    return {r["RegionName"]: r["OptInStatus"] for r in regs}


def aws_up(m, pubkey):
    b3 = boto()
    status = aws_enabled_regions(b3)
    have = {s["name"] for s in m["servers"]}
    for region, city in AWS_REGIONS.items():
        if CITY_FILTER and city not in CITY_FILTER:
            continue
        name = f"aws-{norm(city).replace(' ', '-')}"
        if name in have:
            continue
        st = status.get(region)
        if st is None:
            print(f"  AWS {region} ({city}) does not exist yet; skipped")
            continue
        if st == "not-opted-in":
            print(f"  AWS {region} ({city}) is not enabled on this account; enable it in Account > AWS Regions. Skipped")
            continue
        ec2 = b3.client("ec2", region_name=region)
        info = m["aws"].setdefault(region, {})
        try:
            ec2.import_key_pair(KeyName=TAG, PublicKeyMaterial=pubkey.encode())
        except ec2.exceptions.ClientError as e:
            if "Duplicate" not in str(e):
                raise
        info["key"] = TAG
        if not info.get("sg"):
            vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
            if not vpcs:
                print(f"  AWS {region}: no default VPC; skipped")
                continue
            vpc = vpcs[0]["VpcId"]
            existing = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [TAG]},
                                                             {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
            if existing:
                sg = existing[0]["GroupId"]
            else:
                sg = ec2.create_security_group(GroupName=TAG, Description="fibre ping mesh", VpcId=vpc,
                                               TagSpecifications=[{"ResourceType": "security-group",
                                                                   "Tags": [{"Key": "Project", "Value": TAG}]}])["GroupId"]
                ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[
                    {"IpProtocol": "icmp", "FromPort": -1, "ToPort": -1, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}])
            info["sg"], info["vpc"] = sg, vpc
        save_manifest(m)
        ami = b3.client("ssm", region_name=region).get_parameter(
            Name="/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id")["Parameter"]["Value"]
        subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [info["vpc"]]},
                                                {"Name": "default-for-az", "Values": ["true"]}])["Subnets"]
        r = ec2.run_instances(
            ImageId=ami, InstanceType=AWS_INSTANCE_TYPE, KeyName=TAG, MinCount=1, MaxCount=1,
            NetworkInterfaces=[{"DeviceIndex": 0, "SubnetId": subnets[0]["SubnetId"],
                                "AssociatePublicIpAddress": True, "Groups": [info["sg"]]}],
            TagSpecifications=[{"ResourceType": "instance",
                                "Tags": [{"Key": "Project", "Value": TAG}, {"Key": "Name", "Value": name}]}])
        iid = r["Instances"][0]["InstanceId"]
        m["servers"].append({"name": name, "provider": "aws", "city": city, "region": region, "id": iid,
                             "user": "ubuntu", "ip": None, "plan": AWS_INSTANCE_TYPE, "hourly_usd": None})
        save_manifest(m)
        print(f"  AWS {city:15s} {region:15s} {AWS_INSTANCE_TYPE}  creating")
    aws_lz_up(m, pubkey, b3)


def aws_lz_up(m, pubkey, b3):
    have = {s["name"] for s in m["servers"]}
    for city, lz in AWS_LOCAL_ZONES.items():
        if CITY_FILTER and city not in CITY_FILTER:
            continue
        name = f"aws-{norm(city).replace(' ', '-')}"
        if name in have:
            continue
        region, zone = lz["region"], lz["zone"]
        ec2 = b3.client("ec2", region_name=region)
        try:
            ec2.modify_availability_zone_group(GroupName=lz["group"], OptInStatus="opted-in")
        except ec2.exceptions.ClientError as e:
            print(f"  AWS {city} Local Zone opt-in: {e}")
        try:
            ec2.import_key_pair(KeyName=TAG, PublicKeyMaterial=pubkey.encode())
        except ec2.exceptions.ClientError as e:
            if "Duplicate" not in str(e):
                raise
        vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
        if not vpcs:
            print(f"  AWS {city}: no default VPC in {region}; skipped")
            continue
        vpc = vpcs[0]["VpcId"]
        info = m["aws"].setdefault(region, {})
        sgs = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [TAG]},
                                                    {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
        if sgs:
            sg = sgs[0]["GroupId"]
        else:
            sg = ec2.create_security_group(GroupName=TAG, Description="fibre ping mesh", VpcId=vpc,
                                           TagSpecifications=[{"ResourceType": "security-group",
                                                               "Tags": [{"Key": "Project", "Value": TAG}]}])["GroupId"]
            ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[
                {"IpProtocol": "icmp", "FromPort": -1, "ToPort": -1, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}])
        info["sg"], info["vpc"] = sg, vpc
        subs = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc]},
                                             {"Name": "availability-zone", "Values": [zone]}])["Subnets"]
        if subs:
            subnet = subs[0]["SubnetId"]
        else:
            subnet = None
            for _ in range(30):     # the opt-in can take a little while to apply
                try:
                    subnet = ec2.create_subnet(VpcId=vpc, CidrBlock=lz["cidr"], AvailabilityZone=zone,
                                               TagSpecifications=[{"ResourceType": "subnet",
                                                                   "Tags": [{"Key": "Project", "Value": TAG}]}])["Subnet"]["SubnetId"]
                    break
                except ec2.exceptions.ClientError as e:
                    if "OptIn" in str(e) or "not opted" in str(e).lower() or "InvalidParameterValue" in str(e):
                        time.sleep(10)
                        continue
                    raise
            if not subnet:
                print(f"  AWS {city}: Local Zone not ready yet; run `up` again in a few minutes")
                continue
        info.setdefault("lz_subnets", [])
        if subnet not in info["lz_subnets"]:
            info["lz_subnets"].append(subnet)
        save_manifest(m)
        offered = {o["InstanceType"] for o in ec2.describe_instance_type_offerings(
            LocationType="availability-zone", Filters=[{"Name": "location", "Values": [zone]}])["InstanceTypeOfferings"]}
        itype = next((t for t in LZ_TYPES if t in offered), None)
        if not itype:
            print(f"  AWS {city}: none of {LZ_TYPES} offered in {zone}; skipped")
            continue
        ami = b3.client("ssm", region_name=region).get_parameter(
            Name="/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id")["Parameter"]["Value"]
        root = ec2.describe_images(ImageIds=[ami])["Images"][0]["RootDeviceName"]
        r = ec2.run_instances(
            ImageId=ami, InstanceType=itype, KeyName=TAG, MinCount=1, MaxCount=1,
            BlockDeviceMappings=[{"DeviceName": root, "Ebs": {"VolumeType": "gp2", "VolumeSize": 10,
                                                              "DeleteOnTermination": True}}],
            NetworkInterfaces=[{"DeviceIndex": 0, "SubnetId": subnet, "AssociatePublicIpAddress": True, "Groups": [sg]}],
            TagSpecifications=[{"ResourceType": "instance",
                                "Tags": [{"Key": "Project", "Value": TAG}, {"Key": "Name", "Value": name}]}])
        iid = r["Instances"][0]["InstanceId"]
        m["servers"].append({"name": name, "provider": "aws", "city": city, "region": region, "zone": zone,
                             "id": iid, "user": "ubuntu", "ip": None, "plan": itype, "hourly_usd": None})
        save_manifest(m)
        print(f"  AWS {city:15s} {zone:15s} {itype}  creating (Local Zone)")


def aws_wait(m):
    if not any(s["provider"] == "aws" and not s.get("ip") for s in m["servers"]):
        return
    b3 = boto()
    for s in m["servers"]:
        if s["provider"] != "aws" or s.get("ip"):
            continue
        ec2 = b3.client("ec2", region_name=s["region"])
        ec2.get_waiter("instance_running").wait(InstanceIds=[s["id"]])
        inst = ec2.describe_instances(InstanceIds=[s["id"]])["Reservations"][0]["Instances"][0]
        s["ip"] = inst.get("PublicIpAddress")
        save_manifest(m)
        print(f"  AWS {s['city']:15s} {s['ip']}")


def aws_down(m):
    b3 = boto()
    regions = (set(AWS_REGIONS) | set(m.get("aws", {})) | {lz["region"] for lz in AWS_LOCAL_ZONES.values()}
               | {s["region"] for s in m["servers"] if s["provider"] == "aws"})
    status = aws_enabled_regions(b3)
    for region in sorted(regions):
        if status.get(region) in (None, "not-opted-in"):
            continue
        ec2 = b3.client("ec2", region_name=region)
        res = ec2.describe_instances(Filters=[{"Name": "tag:Project", "Values": [TAG]},
                                              {"Name": "instance-state-name",
                                               "Values": ["pending", "running", "stopping", "stopped"]}])
        ids = [i["InstanceId"] for r in res["Reservations"] for i in r["Instances"]]
        if ids:
            ec2.terminate_instances(InstanceIds=ids)
            print(f"  AWS {region}: terminating {', '.join(ids)}")
            ec2.get_waiter("instance_terminated").wait(InstanceIds=ids)
        for sub in ec2.describe_subnets(Filters=[{"Name": "tag:Project", "Values": [TAG]}])["Subnets"]:
            try:
                ec2.delete_subnet(SubnetId=sub["SubnetId"])
                print(f"  AWS {region}: Local Zone subnet {sub['SubnetId']} deleted")
            except ec2.exceptions.ClientError as e:
                print(f"  AWS {region}: subnet {sub['SubnetId']}: {e}")
        for sg in ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [TAG]}])["SecurityGroups"]:
            try:
                ec2.delete_security_group(GroupId=sg["GroupId"])
            except ec2.exceptions.ClientError as e:
                print(f"  AWS {region}: security group {sg['GroupId']}: {e}")
        try:
            ec2.delete_key_pair(KeyName=TAG)
        except ec2.exceptions.ClientError:
            pass
        print(f"  AWS {region}: clean")
    m["servers"] = [s for s in m["servers"] if s["provider"] != "aws"]
    m["aws"] = {}


# ---------------- SSH helpers ----------------
def ssh_opts(key):
    return ["-i", key, "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={KNOWN}",
            "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR",
            "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=4"]


def ssh(s, key, cmd, timeout=1800):
    return subprocess.run(["ssh", *ssh_opts(key), f"{s['user']}@{s['ip']}", cmd],
                          capture_output=True, text=True, timeout=timeout)


def scp_to(s, key, src, dst):
    return subprocess.run(["scp", "-q", *ssh_opts(key), src, f"{s['user']}@{s['ip']}:{dst}"],
                          capture_output=True, text=True, timeout=120)


def scp_from(s, key, src, dst):
    return subprocess.run(["scp", "-q", *ssh_opts(key), f"{s['user']}@{s['ip']}:{src}", dst],
                          capture_output=True, text=True, timeout=300)


def wait_ssh(s, key):
    for _ in range(60):
        if ssh(s, key, "true", timeout=30).returncode == 0:
            return True
        time.sleep(5)
    return False


# ---------------- run the mesh ----------------
def run_one(s, servers, key, log):
    if not wait_ssh(s, key):
        log(f"  {s['name']}: SSH never answered; skipped")
        return
    ssh(s, key, "mkdir -p mesh/out")
    vp = os.path.join(HERE, "verified_ping.py")
    if not os.path.exists(vp):
        vp = os.path.join(HERE, "verified ping.py")
    scp_to(s, key, vp, "mesh/verified_ping.py")
    peers = "\n".join(f"{p['name']} {p['ip']}" for p in servers if p is not s and p.get("ip")) + "\n"
    peers_file = os.path.join(HERE, f".mesh_peers_{s['name']}.txt")
    with open(peers_file, "w") as fh:
        fh.write(peers)
    scp_to(s, key, peers_file, "mesh/peers.txt")
    os.remove(peers_file)
    cmd = ("cd mesh && rm -f out/* && while read name ip; do "
           f"sudo -n python3 verified_ping.py ping \"$ip\" -c {PING_COUNT} -i {PING_GAP} -W 1 "
           "--csv \"out/$name.csv\" > \"out/$name.log\" 2>&1; done < peers.txt && tar czf out.tgz out")
    r = ssh(s, key, cmd, timeout=3600)
    if r.returncode != 0:
        log(f"  {s['name']}: remote run failed: {r.stderr.strip()[:200]}")
        return
    fetch(s, key, log)


def fetch(s, key, log):
    """Copy a server's finished results back and unpack them."""
    os.makedirs(RAW, exist_ok=True)
    local = os.path.join(RAW, f"{s['name']}.tgz")
    r = scp_from(s, key, "mesh/out.tgz", local)
    if r.returncode != 0 or not os.path.exists(local):
        log(f"  {s['name']}: could not copy results back: {r.stderr.strip()[:200]}")
        return False
    dest = os.path.join(RAW, s["name"])
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(local) as t:
        for mem in t.getmembers():
            if mem.isfile() and mem.name.startswith("out/") and ".." not in mem.name:
                mem.name = os.path.basename(mem.name)
                t.extract(mem, dest)
    log(f"  {s['name']}: done")
    return True


def collect_one(s, servers, key, log):
    """Fetch results a server already finished; never re-pings."""
    if os.path.exists(os.path.join(RAW, f"{s['name']}.tgz")):
        log(f"  {s['name']}: already collected")
        return
    n = len([p for p in servers if p is not s and p.get("ip")])
    r = ssh(s, key, "cd mesh 2>/dev/null && ls out/*.csv 2>/dev/null | wc -l && pgrep -f '[v]erified_ping.py ping' >/dev/null && echo RUNNING || echo IDLE", timeout=60)
    if r.returncode != 0:
        log(f"  {s['name']}: SSH failed: {r.stderr.strip()[:150]}")
        return
    parts = r.stdout.split()
    done = int(parts[0]) if parts and parts[0].isdigit() else 0
    state = parts[-1] if parts else "?"
    if state == "RUNNING":
        log(f"  {s['name']}: still pinging ({done} of {n} peers done); run `collect` again shortly")
        return
    if done == 0:
        log(f"  {s['name']}: no results on the server; it needs `run` again")
        return
    ssh(s, key, "cd mesh && tar czf out.tgz out", timeout=120)
    if done < n:
        log(f"  {s['name']}: only {done} of {n} peers finished; collecting what is there")
    fetch(s, key, log)


def combine(servers):
    by_name = {s["name"]: s for s in servers}
    rows = []
    for s in servers:
        d = os.path.join(RAW, s["name"])
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".csv"):
                continue
            peer = by_name.get(f[:-4])
            if not peer:
                continue
            with open(os.path.join(d, f)) as fh:
                recs = list(csv.DictReader(fh))
            ok = [r for r in recs if r.get("status") == "ok" and r.get("kind") == "echo"]
            full = [r for r in ok if r.get("verify") == "FULL"]
            rtts = [float(r["rtt_ms"]) for r in full if r.get("rtt_ms")]
            kern = [r for r in full if r.get("rtt_kernel_ms")]
            a, b = COORDS.get(s["city"], (None, None)), COORDS.get(peer["city"], (None, None))
            rows.append({
                "src": s["name"], "src_provider": s["provider"], "src_city": s["city"], "src_lat": a[0], "src_lon": a[1],
                "dst": peer["name"], "dst_provider": peer["provider"], "dst_city": peer["city"], "dst_lat": b[0], "dst_lon": b[1],
                "sent": len(recs), "replies": len(ok), "verified_full": len(full), "kernel_stamped": len(kern),
                "min_ms": round(min(rtts), 3) if rtts else None,
                "median_ms": round(statistics.median(rtts), 3) if rtts else None,
            })
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["src"])
        w.writeheader()
        w.writerows(rows)
    return rows


# ---------------- Vultr vs AWS comparison ----------------
def globe_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(h))


def flat_km(a, b):
    k = math.pi * R_EARTH / 180
    r1, r2 = (90 - a[0]) * k, (90 - b[0]) * k
    d = math.radians(b[1] - a[1])
    return math.sqrt(max(0.0, r1 * r1 + r2 * r2 - 2 * r1 * r2 * math.cos(d)))


def vac_ms(km):
    return 2 * km / C_KM_S * 1000


def compare():
    if not os.path.exists(OUT):
        sys.exit("no mesh_pings.csv yet; run `python3 ping_mesh.py run` first")
    best = {}   # (provider-pair, frozenset of cities) -> fastest min_ms over both directions
    with open(OUT) as fh:
        for r in csv.DictReader(fh):
            if not r.get("min_ms"):
                continue
            ms = float(r["min_ms"])
            key = (r["src_provider"], r["dst_provider"], frozenset((r["src_city"], r["dst_city"])))
            if r["src_provider"] != r["dst_provider"]:
                key = ("cross", "cross", key[2])
            if key not in best or ms < best[key]:
                best[key] = ms
    rows = []
    cities = sorted({c for (_, _, pair) in best for c in pair})
    for i, a in enumerate(cities):
        for b in cities[i + 1:]:
            pair = frozenset((a, b))
            v = best.get(("vultr", "vultr", pair))
            w = best.get(("aws", "aws", pair))
            if v is None and w is None:
                continue
            pa, pb = COORDS.get(a), COORDS.get(b)
            g = globe_km(pa, pb) if pa and pb else None
            f = flat_km(pa, pb) if pa and pb else None
            fastest = min(x for x in (v, w) if x is not None)
            rows.append({
                "city_a": a, "city_b": b, "globe_km": round(g, 1) if g else None, "flat_km": round(f, 1) if f else None,
                "vultr_min_ms": v, "aws_min_ms": w,
                "difference_ms": round(v - w, 3) if v is not None and w is not None else None,
                "faster_network": ("vultr" if v < w else "aws") if v is not None and w is not None else None,
                "globe_floor_c_ms": round(vac_ms(g), 2) if g else None,
                "flat_floor_c_ms": round(vac_ms(f), 2) if f else None,
                "vultr_headroom_globe": round(v - vac_ms(g), 2) if v is not None and g else None,
                "aws_headroom_globe": round(w - vac_ms(g), 2) if w is not None and g else None,
                "vultr_headroom_flat": round(v - vac_ms(f), 2) if v is not None and f else None,
                "aws_headroom_flat": round(w - vac_ms(f), 2) if w is not None and f else None,
                "fastest_headroom_flat": round(fastest - vac_ms(f), 2) if f else None,
            })
    same_city = [(c, best[("cross", "cross", frozenset((c,)))]) for c in cities
                 if ("cross", "cross", frozenset((c,))) in best]
    with open(CMP, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["city_a"])
        w.writeheader()
        w.writerows(rows)
    both = [r for r in rows if r["difference_ms"] is not None]
    print(f"\n== Vultr vs AWS: {len(both)} city pairs measured on both networks ==")
    print(f"{'pair':28s} {'globe km':>9s} {'Vultr ms':>9s} {'AWS ms':>8s} {'diff':>7s}  {'c floor globe':>13s} {'c floor flat':>12s}")
    for r in sorted(both, key=lambda r: r["globe_km"] or 0):
        print(f"{r['city_a'] + ' - ' + r['city_b']:28s} {r['globe_km'] or 0:9,.0f} {r['vultr_min_ms']:9.1f} {r['aws_min_ms']:8.1f} "
              f"{r['difference_ms']:+7.1f}  {r['globe_floor_c_ms'] or 0:13.1f} {r['flat_floor_c_ms'] or 0:12.1f}")
    if both:
        aws_faster = sum(1 for r in both if r["faster_network"] == "aws")
        print(f"AWS faster on {aws_faster} of {len(both)} pairs; median difference "
              f"{statistics.median(r['difference_ms'] for r in both):+.1f} ms (Vultr minus AWS).")
    under_g = [r for r in rows for n in ("vultr", "aws")
               if r[f"{n}_headroom_globe"] is not None and r[f"{n}_headroom_globe"] < 0]
    under_f = [r for r in rows if r["fastest_headroom_flat"] is not None and r["fastest_headroom_flat"] < 0]
    print(f"Pairs faster than light over globe distance: {len(under_g)}")
    print(f"Pairs faster than light over flat-map distance: {len(under_f)}"
          + ("  -> " + ", ".join(f"{r['city_a']}-{r['city_b']} ({r['fastest_headroom_flat']:+.1f} ms)" for r in under_f) if under_f else ""))
    if same_city:
        print("\n== Location check: Vultr and AWS servers in the same city ==")
        for c, ms in same_city:
            print(f"  {c:15s} {ms:6.2f} ms" + ("   (over 5 ms: check this pair)" if ms > 5 else ""))
    print(f"\nSaved {os.path.basename(CMP)}")


# ---------------- commands ----------------
def cmd_up(a):
    pub = os.path.expanduser(a.key) + ".pub"
    if not os.path.exists(pub):
        sys.exit(f"no public key at {pub}; make one with: ssh-keygen -t ed25519")
    pubkey = open(pub).read().strip()
    n_v = 0 if a.aws_only else len(CITY_FILTER or VULTR_CITIES)
    n_a = 0 if a.vultr_only else len([c for c in list(AWS_REGIONS.values()) + list(AWS_LOCAL_ZONES)
                                      if not CITY_FILTER or c in CITY_FILTER])
    print(f"This creates up to {n_v} Vultr and {n_a} AWS servers, billed by the hour until `down`.")
    print(f"Rough cost: Vultr ~$0.007-0.01/h each, AWS t3.micro + public IPv4 ~$0.02/h each "
          f"(about ${n_v * 0.01 + n_a * 0.02:.2f} per hour for this mesh).")
    if not a.yes and input("Type yes to continue: ").strip().lower() != "yes":
        sys.exit("cancelled")
    m = load_manifest()
    if not a.aws_only:
        vultr_up(m, pubkey)
    if not a.vultr_only:
        aws_up(m, pubkey)
    print("Waiting for addresses...")
    if not a.aws_only:
        vultr_wait(m)
        m["servers"] = [x for x in m["servers"] if not x.get("gone")]
        save_manifest(m)
    if not a.vultr_only:
        aws_wait(m)
    cmd_status(a)
    print("\nNext: python3 ping_mesh.py run      (and `down` when finished)")


def cmd_status(a):
    m = load_manifest()
    if not m["servers"]:
        print("no servers in mesh_servers.json")
        return
    for s in m["servers"]:
        print(f"  {s['name']:22s} {s['provider']:5s} {s['city']:15s} {s['region']:15s} {s.get('ip') or '(no ip yet)'}")
    print(f"  {len(m['servers'])} servers")


def cmd_run(a):
    m = load_manifest()
    servers = [s for s in m["servers"] if s.get("ip")]
    if len(servers) < 2:
        sys.exit("need at least two running servers; run `up` first")
    key = os.path.expanduser(a.key)
    lock = threading.Lock()
    def log(msg):
        with lock:
            print(msg, flush=True)
    print(f"{len(servers)} servers, {len(servers) * (len(servers) - 1)} directed pairs, "
          f"{PING_COUNT} echoes each. This takes a few minutes.")
    threads = [threading.Thread(target=run_one, args=(s, servers, key, log)) for s in servers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    rows = combine(servers)
    good = [r for r in rows if r["min_ms"] is not None]
    print(f"\nSaved {os.path.basename(OUT)}: {len(good)} of {len(rows)} pairs with verified replies.")
    if any(s["provider"] == "aws" for s in servers) and any(s["provider"] == "vultr" for s in servers):
        compare()
    print("Run `python3 ping_mesh.py down` when you have what you need.")


def cmd_collect(a):
    m = load_manifest()
    servers = [s for s in m["servers"] if s.get("ip")]
    key = os.path.expanduser(a.key)
    lock = threading.Lock()
    def log(msg):
        with lock:
            print(msg, flush=True)
    threads = [threading.Thread(target=collect_one, args=(s, servers, key, log)) for s in servers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    rows = combine(servers)
    good = [r for r in rows if r["min_ms"] is not None]
    got = len([s for s in servers if os.path.exists(os.path.join(RAW, f"{s['name']}.tgz"))])
    print(f"\nCollected {got} of {len(servers)} servers. Saved {os.path.basename(OUT)}: "
          f"{len(good)} of {len(rows)} pairs with verified replies.")
    if any(s["provider"] == "aws" for s in servers) and any(s["provider"] == "vultr" for s in servers):
        compare()


def cmd_compare(a):
    compare()


def cmd_down(a):
    m = load_manifest()
    if not a.aws_only:
        if os.environ.get("VULTR_API_KEY"):
            vultr_down(m)
        else:
            print("VULTR_API_KEY not set; Vultr servers (if any) left running")
    if not a.vultr_only:
        if AWS_REGIONS or m.get("aws"):
            aws_down(m)
    save_manifest(m)
    print("Done. Check status shows nothing left:  python3 ping_mesh.py status")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["up", "status", "run", "collect", "compare", "down"])
    ap.add_argument("--key", default="~/.ssh/id_ed25519", help="private SSH key; the .pub beside it is uploaded")
    ap.add_argument("--vultr-only", action="store_true")
    ap.add_argument("--aws-only", action="store_true")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation on `up`")
    ap.add_argument("--cities", nargs="+", default=[], help="only create servers in these cities, e.g. --cities Santiago \"Sao Paulo\"")
    a = ap.parse_args()
    CITY_FILTER[:] = a.cities
    {"up": cmd_up, "status": cmd_status, "run": cmd_run, "collect": cmd_collect, "compare": cmd_compare, "down": cmd_down}[a.command](a)


if __name__ == "__main__":
    main()

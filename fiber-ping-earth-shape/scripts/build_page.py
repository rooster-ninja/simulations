#!/usr/bin/env python3
"""Embed data/summary.json into scripts/page.template.html -> index.html."""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(HERE, "data", "summary.json")))
tpl = open(os.path.join(HERE, "scripts", "page.template.html")).read()
open(os.path.join(HERE, "index.html"), "w").write(tpl.replace("/*DATA*/", json.dumps(data, separators=(",", ":"))))
print("wrote index.html")

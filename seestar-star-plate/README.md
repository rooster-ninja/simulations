# Seestar S30 star plate

Shows how small an arcsecond is at the Seestar S30's plate scale.

## What it shows

- A simulated 1920 × 1080 frame at about 3.99″/pixel (30 mm aperture, 150 mm focal length, 2.9 µm pixels), giving a field of about 2.1° × 1.2°.
- A zoom slider from the full frame down to about 25″ across, with preset buttons.
- An adaptive scale bar in arcseconds, arcminutes or degrees, also given in pixels.
- Overlays that appear at suitable zooms: the full Moon (31′), a 10″ FWHM star profile, a 1″ box, and Barnard's Star's parallax ellipse (±0.55″).

## Model and simplifications

- Stars are Gaussian PSFs with 10″ FWHM, standing in for diffraction plus seeing. The brightness distribution is a rough power law from a fixed random seed.
- Background is a flat sky level with approximate Gaussian noise, displayed with an asinh stretch.
- No optical distortion, vignetting, hot pixels, colour, or Bayer pattern.
- The parallax ellipse is illustrative, not computed for a real ecliptic latitude.
- Specs are approximate.

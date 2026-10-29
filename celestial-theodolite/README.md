# Celestial Theodolite: planar prediction

Star occultations behind distant mountain peaks, worked on a flat plane.
At T = 0 the star sits on the peak's skyline as seen from the observer (O₁).
The observer is then moved to the peak (O₂) at the same instant, and the
star's elevation from each place is compared.

## What it shows

- **Celestial spheres at O₁ and O₂.** Each observer sits at the centre of
  its own celestial sphere, with the horizon through the centre and zenith
  at the top. The ground and the peak line carry a parallel constraint.
- **θ₁** is the elevation angle from O₁ to the peak summit, from the
  peak–observer right triangle: `θ₁ = atan(Δh / D)`, where
  `Δh = peak elevation − observer elevation` and `D` is the ground distance.
- **θ₂** is the recorded elevation of the star with the observer at the
  peak (Star→Peak ♈︎ from the data table). The page shows `θ₂ − θ₁`.
- **♈︎Δ** (purple) is the recorded shift, `Star→Peak ♈︎ − Star→Obs ♈︎`,
  drawn as a wedge anchored at P₂ and tied to the surface distance `D`.

All angles are shown as DD°MM′SS″.

## Data

The peak list is embedded from the Celestial Theodolite Calculator v9.1.1
data table (peak, star, date and time, UTC offset as recorded, coordinates,
elevations, distance, and the ♈︎ and ϵ Star→Peak / Star→Obs columns).

## Simplifications

- Angles are drawn larger than true so they can be seen; every number is
  computed from the data.
- The purple wedge uses a square-root scale (about 54′, roughly a 100 km
  baseline, draws at 14°).
- No refraction or deflection of the vertical.
- The globe prediction is a separate page still to come.

# Handoff

## Project State

All three integration components are implemented and functional:
- **Experience Builder Widget** (`experience-builder/`) - v1.0.0, targets ExB 1.14.0
- **ArcGIS Pro Toolbox** (`arcgis-pro/`) - targets Pro 3.2-3.7+
- **Survey123 Integration** (`survey123/`) - Make.com webhook pipeline

## Recent Changes

- Renamed bare `township` identifiers to `township_canada` across the codebase (commit 994b827)
- Added CI workflow and MIT LICENSE (commit a51fb67)

## Known Considerations

- Trial vs paid API endpoints must be configured correctly (`isTrialKey` flag in ExB widget)
- Centroid assumed at index 1 in GeoJSON features array -- fragile if API changes response order
- Survey123 integration requires manual Make.com scenario setup (no native webhook support)
- CI workflow exists at `.github/workflows/` but was removed from yaml count (0 detected by health audit -- verify if still active)

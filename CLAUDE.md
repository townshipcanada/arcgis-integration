# Township Canada ArcGIS Integration

Multi-platform suite that converts Canadian legal land descriptions (DLS, NTS, Geographic Townships) to GPS coordinates across the ArcGIS ecosystem using the Township Canada API.

## Components

| Component | Path | Tech | Language |
|-----------|------|------|----------|
| Experience Builder Widget | `experience-builder/` | React + Jimu UI (ExB 1.14.0) | TypeScript/TSX |
| ArcGIS Pro Toolbox | `arcgis-pro/` | arcpy locator | Python 3.9+ |
| Survey123 Integration | `survey123/` | Make.com webhook | JSON config |

## Key Conventions

- API key passed as `X-API-Key` header (never URL param)
- API endpoint: `https://developer.townshipcanada.com`
- User-Agent: `townshipcanada-<platform>/<version>`
- GeoJSON coordinates are `[longitude, latitude]`
- Centroid is at index 1 in the features array
- CSS classes use `township-canada-` prefix
- Python files use snake_case; TS exports use PascalCase

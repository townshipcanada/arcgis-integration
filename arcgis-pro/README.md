# Township Canada — ArcGIS Pro Integration

Convert Canadian legal land descriptions (DLS, NTS, Geographic Townships) to GPS coordinates directly from ArcGIS Pro.

## Features

- **Search Bar Integration**: Type legal land descriptions in ArcGIS Pro's Locate pane
- **Autocomplete**: Get suggestions as you type
- **Batch Conversion**: Convert an entire table of legal land descriptions to a point feature class
- **Reverse Geocoding**: Right-click any point on the map to find its legal land description
- **Boundary Polygons**: Optionally output section/quarter-section boundary polygons

## Requirements

- ArcGIS Pro 3.2 or later (tested up to 3.7)
- Township Canada API key ([get one here](https://townshipcanada.com/developers))
- Internet connection

## Installation

### 1. Download the toolbox

Copy the `arcgis-pro/` folder to a location on your machine, for example:

```
C:\Users\<you>\Documents\ArcGIS\TownshipCanada\
```

### 2. Add the toolbox to ArcGIS Pro

1. Open ArcGIS Pro
2. In the **Catalog** pane, right-click **Toolboxes**
3. Click **Add Toolbox**
4. Navigate to the folder and select `TownshipCanada.pyt`

### 3. Configure your API key

1. Expand the **Township Canada** toolbox in the Catalog pane
2. Double-click **Configure API Key**
3. Paste your Township Canada API key and click **Run**

Alternatively, set the `TOWNSHIP_CANADA_API_KEY` environment variable.

## Usage

### Search a single location

1. Open the **Township Canada** toolbox
2. Run **Search Legal Land Description**
3. Type a legal land description, e.g.:
   - `NW-36-42-3-W5` (DLS — Alberta)
   - `A-2-F/93-P-8` (NTS — British Columbia)
   - `Lot 2 Con 4 Osprey` (Geographic Township — Ontario)
4. The result is displayed in the messages and optionally added to the map

### Batch conversion

1. Open the **Township Canada** toolbox
2. Run **Convert Legal Land Descriptions**
3. Select your input table (CSV, Excel, geodatabase table, or feature class)
4. Choose the field containing legal land descriptions
5. Specify an output feature class location
6. Optionally check **Include Boundary Polygons** to also output section/quarter boundaries
7. Click **Run**

### Locate pane integration

To use Township Canada in the ArcGIS Pro search bar:

1. Open the **Locate** pane (Map tab > Inquiry group > Locate)
2. Click the settings gear icon
3. Under **Providers**, click **Add** > **Custom Provider**
4. Point to `township_canada_locator.py` in this folder
5. Legal land descriptions will now appear as search results

## Supported Formats

| System                            | Province(s)    | Example                |
| --------------------------------- | -------------- | ---------------------- |
| DLS (Dominion Land Survey)        | AB, SK, MB     | `NW-36-42-3-W5`        |
| LSD (Legal Subdivision)           | AB, SK, MB     | `10-36-42-3-W5`        |
| NTS (National Topographic System) | BC             | `A-2-F/93-P-8`         |
| Geographic Townships              | ON             | `Lot 2 Con 4 Osprey`   |
| UWI (Unique Well Identifier)      | AB, SK, MB, BC | `100/06-36-042-03W5/0` |

## API Key

Get your API key at [townshipcanada.com/developers](https://townshipcanada.com/developers).

| Tier         | Requests/mo | Price   |
| ------------ | ----------- | ------- |
| Starter      | 1,000       | $20/mo  |
| Professional | 10,000      | $100/mo |
| Enterprise   | 100,000     | $500/mo |

## Troubleshooting

**"API key not configured"**: Run the Configure API Key tool or set the `TOWNSHIP_CANADA_API_KEY` environment variable.

**"Could not connect to Township Canada API"**: Check your internet connection and firewall settings. The tool needs HTTPS access to `developer.townshipcanada.com`.

**Slow batch conversion**: The tool makes one API call per description. For large datasets (1,000+), consider using the [Township Canada Python SDK](https://pypi.org/project/townshipcanada/) with batch endpoints for better throughput.

## License

MIT License. Copyright (c) Maps & Apps Inc.

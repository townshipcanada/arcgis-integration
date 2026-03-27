# Township Canada — ArcGIS Integration

Convert Canadian legal land descriptions (DLS, NTS, Geographic Townships) to GPS coordinates across the ArcGIS ecosystem.

## Components

| Component                                          | Platform         | Description                                                                                 |
| -------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------- |
| [ArcGIS Pro Toolbox](./arcgis-pro/)                | ArcGIS Pro 3.2+  | Python toolbox with locator role, batch conversion, and single search tools                 |
| [Experience Builder Widget](./experience-builder/) | ArcGIS Online    | Custom widget for web maps with search, autocomplete, reverse geocode, and boundary display |
| [Survey123 Integration](./survey123/)              | ArcGIS Survey123 | Webhook-based pipeline via Make.com for field data collection workflows                     |

## Quick Start

### ArcGIS Pro

```
1. Copy arcgis-pro/ to your machine
2. Add TownshipCanada.pyt as a toolbox in ArcGIS Pro
3. Run "Configure API Key" with your Township Canada API key
4. Search legal land descriptions from the Locate pane or batch convert a table
```

### ArcGIS Online (Experience Builder)

```
1. Copy experience-builder/ into your Experience Builder's custom widgets folder
2. Add the "Township Canada" widget to your experience
3. Configure your API key and connect to a Map widget
4. Search legal land descriptions or click the map for reverse geocode
```

### Survey123

```
1. Create a Survey123 form with a legal_description text field
2. Import survey123/make-scenario.json into Make.com
3. Set your Township Canada API key and ArcGIS token in Make.com
4. Add the Make.com webhook URL to your Survey123 webhook settings
5. Submitted descriptions are automatically converted to coordinates
```

## Supported Formats

| System                            | Province(s)    | Example                |
| --------------------------------- | -------------- | ---------------------- |
| DLS (Dominion Land Survey)        | AB, SK, MB     | `NW-36-42-3-W5`        |
| LSD (Legal Subdivision)           | AB, SK, MB     | `10-36-42-3-W5`        |
| NTS (National Topographic System) | BC             | `A-2-F/93-P-8`         |
| Geographic Townships              | ON             | `Lot 2 Con 4 Osprey`   |
| UWI (Unique Well Identifier)      | AB, SK, MB, BC | `100/06-36-042-03W5/0` |

## API Key

All components require a Township Canada API key from [townshipcanada.com/developers](https://townshipcanada.com/developers).

## Environment Variables

| Variable                  | Used By              | Description                                   |
| ------------------------- | -------------------- | --------------------------------------------- |
| `TOWNSHIP_CANADA_API_KEY` | All components       | Your Township Canada API key                  |
| `ARCGIS_TOKEN`            | Survey123 (Make.com) | ArcGIS Online token for feature layer updates |

## Marketplace

See [MARKETPLACE.md](./MARKETPLACE.md) for ArcGIS Marketplace listing details, screenshots requirements, and demo video outline.

## License

MIT License. Copyright (c) Maps & Apps Inc.

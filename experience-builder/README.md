# Township Canada — ArcGIS Experience Builder Widget

A custom widget for ArcGIS Experience Builder that lets users convert Canadian legal land descriptions (DLS, NTS, Geographic Townships) to GPS coordinates directly in web maps.

## Features

- **Search**: Type a legal land description and get coordinates plotted on the map
- **Autocomplete**: Suggestions appear as you type
- **Boundary Polygons**: Section/quarter-section boundaries drawn on the map
- **Reverse Geocode**: Click anywhere on the map to find the legal land description
- **Configurable**: API key, zoom behavior, and boundary display via widget settings

## Requirements

- ArcGIS Experience Builder 1.14+
- Township Canada API key ([get one here](https://townshipcanada.com/developers))

## Installation

### For Experience Builder (Developer Edition)

1. Copy the `experience-builder/` folder into your Experience Builder's `client/your-extensions/widgets/` directory:

```bash
cp -r experience-builder/ <exb-root>/client/your-extensions/widgets/township-canada/
```

2. Start Experience Builder and the widget will appear in the widget panel under "Custom".

### For ArcGIS Online (via custom widget upload)

1. Zip the `experience-builder/` folder contents
2. In ArcGIS Online, go to **Content** > **My Content** > **Add Item**
3. Upload the zip as a **Web Experience Widget**
4. The widget will be available when building experiences

## Configuration

After adding the widget to your experience:

1. Click the widget to open its settings panel
2. Enter your **Township Canada API key**
3. Connect the widget to a **Map widget** in your experience
4. Configure display options:
   - **Show boundary polygons**: Draw section/quarter boundaries on the map
   - **Zoom to result**: Automatically zoom when a result is found
   - **Zoom level**: How far to zoom in (1-20)
   - **Enable reverse geocode**: Allow click-on-map to find legal descriptions

## Supported Formats

| System                            | Province(s) | Example              |
| --------------------------------- | ----------- | -------------------- |
| DLS (Dominion Land Survey)        | AB, SK, MB  | `NW-36-42-3-W5`      |
| LSD (Legal Subdivision)           | AB, SK, MB  | `10-36-42-3-W5`      |
| NTS (National Topographic System) | BC          | `A-2-F/93-P-8`       |
| Geographic Townships              | ON          | `Lot 2 Con 4 Osprey` |

## License

MIT License. Copyright (c) Maps & Apps Inc.

# Township Canada — Survey123 Integration

Convert legal land descriptions to GPS coordinates in ArcGIS Survey123 field data collection workflows using webhooks and Make.com (formerly Integromat).

## Overview

Survey123 doesn't support custom geocoding providers natively. This integration uses a **webhook + Make.com** pipeline to:

1. Field worker enters a legal land description in a Survey123 form
2. On submit, a webhook fires to Make.com
3. Make.com calls the Township Canada API to convert the description to coordinates
4. The coordinates are written back to the feature layer as a point geometry

This enables field crews to collect data by legal land description (which they know) rather than GPS coordinates (which they may not have).

## Architecture

```
Survey123 Form
    ↓ (webhook on submit)
Make.com Scenario
    ↓ (HTTP call)
Township Canada API
    ↓ (coordinates returned)
Make.com
    ↓ (update feature)
ArcGIS Online Feature Layer
```

## Setup

### Step 1: Create the Survey123 form

Design your Survey123 form with these fields:

| Field               | Type       | Purpose                                                |
| ------------------- | ---------- | ------------------------------------------------------ |
| `legal_description` | Text       | The legal land description entered by the field worker |
| `description_type`  | Select One | DLS, NTS, or Geographic Township                       |
| `latitude`          | Decimal    | Auto-populated by Make.com after conversion            |
| `longitude`         | Decimal    | Auto-populated by Make.com after conversion            |
| `province`          | Text       | Auto-populated by Make.com after conversion            |
| `conversion_status` | Text       | "pending", "success", or "failed"                      |

Set `latitude`, `longitude`, `province`, and `conversion_status` as hidden fields with default values (`0`, `0`, empty, and `pending`).

#### XLSForm example

```
| type          | name               | label                      | default   | appearance |
|---------------|--------------------|----------------------------|-----------|------------|
| text          | legal_description  | Legal Land Description      |           |            |
| select_one ds | description_type   | Description Type            | dls       |            |
| hidden        | latitude           |                            | 0         |            |
| hidden        | longitude          |                            | 0         |            |
| hidden        | province           |                            |           |            |
| hidden        | conversion_status  |                            | pending   |            |
|               |                    |                            |           |            |
| list_name     | name               | label                      |           |            |
| ds            | dls                | DLS (AB, SK, MB)           |           |            |
| ds            | nts                | NTS (BC)                   |           |            |
| ds            | gts                | Geographic Township (ON)   |           |            |
```

### Step 2: Configure the Survey123 webhook

1. Open your survey in the Survey123 website
2. Go to **Settings** > **Webhooks**
3. Add a new webhook:
   - **Name**: Township Canada Conversion
   - **Target URL**: Your Make.com webhook URL (from Step 3)
   - **Trigger events**: New submission
   - **Payload**: Include `objectId`, `legal_description`, `description_type`

### Step 3: Create the Make.com scenario

Import the provided `make-scenario.json` blueprint into Make.com, or build it manually:

#### Module 1: Webhook (trigger)

- Type: **Custom webhook**
- Receives the Survey123 submission payload

#### Module 2: HTTP Request (Township Canada API)

- **URL**: `https://developer.townshipcanada.com/search/legal-location`
- **Method**: GET
- **Query parameters**:
  - `location`: `{{1.legal_description}}`
- **Headers**:
  - `X-API-Key`: Your Township Canada API key (trial or paid)
  - `Accept`: `application/json`

> For trial keys, change the base URL to `https://townshipcanada.com/api/integrations/trial` — the path and response format are identical.

#### Module 3: Parse JSON

- Parse the GeoJSON FeatureCollection response
- The centroid feature (`properties.shape == "centroid"`) contains the point coordinates
- Extract `features[1].geometry.coordinates[0]` (longitude) and `features[1].geometry.coordinates[1]` (latitude). GeoJSON uses `[longitude, latitude]` order.
- Extract `features[1].properties.province`
- **Note:** The index `[1]` assumes the centroid feature (`properties.shape == "centroid"`) is the second element. Adjust if your response order differs.

#### Module 4: HTTP Request (Update feature layer)

- **URL**: `https://services.arcgis.com/<your-org>/arcgis/rest/services/<your-service>/FeatureServer/0/updateFeatures`
- **Method**: POST
- **Body** (form-urlencoded):
  ```
  f=json
  token=<your-arcgis-token>
  features=[{"attributes":{"objectId":{{1.objectId}},"latitude":{{3.latitude}},"longitude":{{3.longitude}},"province":"{{3.province}}","conversion_status":"success"},"geometry":{"x":{{3.longitude}},"y":{{3.latitude}},"spatialReference":{"wkid":4326}}}]
  ```

#### Module 5: Error handler (optional)

If Module 2 or 4 fails, update the feature with `conversion_status = "failed"`.

### Step 4: Test the pipeline

1. Submit a test survey with a known legal land description (e.g., `NW-36-42-3-W5`)
2. Check Make.com scenario execution logs
3. Verify the feature layer has updated coordinates

## Cascading Select for DLS

For a better field experience, you can use cascading selects so field workers pick township, range, and meridian from dropdowns instead of typing:

```
| type                    | name     | label    | choice_filter           |
|-------------------------|----------|----------|-------------------------|
| select_one meridian     | meridian | Meridian |                         |
| select_one range_list   | range    | Range    | meridian=${meridian}    |
| select_one township_list| township | Township |                         |
| select_one section_list | section  | Section  |                         |
| select_one quarter_list | quarter  | Quarter  |                         |
```

The `legal_description` field can then be a calculate type that concatenates the selections:

```
| type      | name               | calculation                                                    |
|-----------|--------------------|----------------------------------------------------------------|
| calculate | legal_description  | concat(${quarter}, '-', ${section}, '-', ${township}, '-', ${range}, '-W', ${meridian}) |
```

## API Key

Get a free trial key at [townshipcanada.com/api/try?ref=arcgis-survey123](https://townshipcanada.com/api/try?ref=arcgis-survey123) or a paid key at [townshipcanada.com/developers](https://townshipcanada.com/developers).

Both trial and paid keys work with this integration. Trial keys are valid for 7 days with a limited number of API calls.

## Environment Variables

| Variable                  | Description                                                                    |
| ------------------------- | ------------------------------------------------------------------------------ |
| `TOWNSHIP_CANADA_API_KEY` | Your Township Canada API key — trial or paid (used in Make.com HTTP module)    |

## Error Codes

| Status | Meaning              | Action                                                  |
| ------ | -------------------- | ------------------------------------------------------- |
| 401    | Invalid API key      | Check that your API key is correct                     |
| 403    | Trial expired        | Trial period ended — upgrade to a paid key              |
| 429    | Trial limit reached  | Usage limit exceeded — upgrade or wait for next period  |

## Troubleshooting

**Webhook not firing**: Ensure the webhook is enabled in Survey123 settings and the target URL is correct.

**API returns 401**: Check that your API key is valid. If using a trial key, ensure it hasn't expired.

**API returns 403**: Your trial key has expired. Upgrade to a paid key at [townshipcanada.com/developers](https://townshipcanada.com/developers).

**API returns 429**: Your trial key has reached its usage limit. Upgrade to a paid key.

**Coordinates not updating in feature layer**: Verify the ArcGIS token has edit permissions on the feature layer. Tokens expire — consider using an OAuth app for long-lived access.

**Make.com scenario errors**: Check the execution logs in Make.com. The most common issues are malformed JSON payloads and expired ArcGIS tokens.

## License

MIT License. Copyright (c) Maps & Apps Inc.

"""
Township Canada Locator for ArcGIS Pro.

A custom geocoding locator role that converts Canadian legal land descriptions
(DLS, NTS, Geographic Townships) to GPS coordinates using the Township Canada API.

Integrates with ArcGIS Pro's Locate pane so users can search by legal land
description directly from the search bar.

Requirements:
    - ArcGIS Pro 3.2+ (tested up to 3.7)
    - Python 3.9+ (bundled with ArcGIS Pro)
    - Township Canada API key (https://townshipcanada.com/developers)
"""

import json
import os
import re
import urllib.request
import urllib.error
import urllib.parse

import arcpy

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = "https://developer.townshipcanada.com"
USER_AGENT = "townshipcanada-arcgis-pro/1.0.0"

# Patterns that indicate a Canadian legal land description
DLS_PATTERN = re.compile(
    r"(?:(?:NE|NW|SE|SW|N|S|E|W)\s*[-]?\s*)?"
    r"\d{1,2}\s*[-]\s*\d{1,3}\s*[-]\s*\d{1,2}\s*[-]\s*W\s*[1-6]",
    re.IGNORECASE,
)
LSD_PATTERN = re.compile(
    r"\d{1,2}\s*[-]\s*\d{1,2}\s*[-]\s*\d{1,3}\s*[-]\s*\d{1,2}\s*[-]\s*W\s*[1-6]",
    re.IGNORECASE,
)
NTS_PATTERN = re.compile(
    r"[A-D]\s*[-]?\s*\d{1,2}\s*[-]?\s*[A-L]\s*/?\s*\d{2,3}\s*[-]?\s*[A-P]\s*[-]?\s*\d{1,2}",
    re.IGNORECASE,
)
GTS_PATTERN = re.compile(
    r"(?:lot|con|concession)\s+\d+",
    re.IGNORECASE,
)


def _get_api_key():
    """Retrieve the Township Canada API key from environment or ArcGIS Pro settings."""
    # Check environment variable first
    api_key = os.environ.get("TOWNSHIP_CANADA_API_KEY", "")
    if api_key:
        return api_key

    # Check ArcGIS Pro project settings file
    config_path = os.path.join(
        os.path.expanduser("~"),
        ".townshipcanada",
        "config.json",
    )
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            return config.get("api_key", "")

    return ""


def _api_request(endpoint, params=None):
    """Make an authenticated GET request to the Township Canada API.

    Args:
        endpoint: API endpoint path (e.g., "/search/legal-location").
        params: Dictionary of query parameters.

    Returns:
        Parsed JSON response as a dictionary.

    Raises:
        RuntimeError: If the API request fails.
    """
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "Township Canada API key not configured. "
            "Set the TOWNSHIP_CANADA_API_KEY environment variable or run "
            "the configuration tool."
        )

    url = API_BASE_URL + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url)
    req.add_header("X-API-Key", api_key)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Township Canada API error ({e.code}): {body}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Could not connect to Township Canada API: {e.reason}"
        ) from e


def _parse_feature_collection(fc):
    """Extract centroid coordinates and metadata from a GeoJSON FeatureCollection.

    Args:
        fc: GeoJSON FeatureCollection dict.

    Returns:
        Tuple of (longitude, latitude, legal_location, province, survey_system, boundary_geojson).
    """
    centroid = None
    grid = None

    for feature in fc.get("features", []):
        props = feature.get("properties", {})
        if props.get("shape") == "centroid":
            centroid = feature
        elif props.get("shape") == "grid":
            grid = feature

    if not centroid:
        return None

    coords = centroid["geometry"]["coordinates"]
    props = centroid.get("properties", {})

    boundary = None
    if grid and grid.get("geometry"):
        boundary = grid["geometry"]

    return (
        coords[0],  # longitude
        coords[1],  # latitude
        props.get("legal_location", ""),
        props.get("province", ""),
        props.get("survey_system", ""),
        boundary,
    )


def _is_legal_description(text):
    """Check if text looks like a Canadian legal land description."""
    text = text.strip()
    return bool(
        DLS_PATTERN.search(text)
        or LSD_PATTERN.search(text)
        or NTS_PATTERN.search(text)
        or GTS_PATTERN.search(text)
    )


# ---------------------------------------------------------------------------
# ArcGIS Pro Geocoding Functions
# ---------------------------------------------------------------------------


class TownshipCanadaLocator:
    """Custom locator role for ArcGIS Pro that geocodes Canadian legal land descriptions.

    Usage:
        1. Add this locator to ArcGIS Pro via the Locate pane settings.
        2. Type a legal land description (e.g., "NW-36-42-3-W5") in the search bar.
        3. Results appear as map locations with boundary polygons.
    """

    def __init__(self):
        self.name = "Township Canada"
        self.description = (
            "Convert Canadian legal land descriptions (DLS, NTS, Geographic Townships) "
            "to GPS coordinates"
        )
        self.category = "Legal Land Descriptions"

    def geocode(self, location):
        """Geocode a legal land description to coordinates.

        Args:
            location: Legal land description string.

        Returns:
            List of result dictionaries with coordinates and metadata.
        """
        location = location.strip()
        if not location:
            return []

        try:
            fc = _api_request(
                "/search/legal-location",
                params={"location": location},
            )
        except RuntimeError as e:
            arcpy.AddWarning(str(e))
            return []

        parsed = _parse_feature_collection(fc)
        if not parsed:
            return []

        lon, lat, legal_loc, province, survey_system, boundary = parsed

        result = {
            "address": legal_loc,
            "location": arcpy.PointGeometry(
                arcpy.Point(lon, lat),
                arcpy.SpatialReference(4326),
            ),
            "score": 100,
            "attributes": {
                "LegalLocation": legal_loc,
                "Province": province,
                "SurveySystem": survey_system,
                "Latitude": lat,
                "Longitude": lon,
            },
        }

        return [result]

    def suggest(self, text, max_suggestions=5):
        """Get autocomplete suggestions for a partial legal land description.

        Args:
            text: Partial search query.
            max_suggestions: Maximum number of suggestions to return.

        Returns:
            List of suggestion dictionaries.
        """
        text = text.strip()
        if len(text) < 2:
            return []

        try:
            fc = _api_request(
                "/autocomplete/legal-location",
                params={
                    "location": text,
                    "limit": min(max_suggestions, 10),
                },
            )
        except RuntimeError:
            return []

        suggestions = []
        for feature in fc.get("features", []):
            props = feature.get("properties", {})
            legal_loc = props.get("legal_location", "")
            if legal_loc:
                suggestions.append({
                    "text": legal_loc,
                    "isCollection": False,
                })

        return suggestions

    def reverse_geocode(self, location):
        """Find the legal land description at given coordinates.

        Args:
            location: arcpy.PointGeometry or (longitude, latitude) tuple.

        Returns:
            Dictionary with the legal land description, or None.
        """
        if isinstance(location, arcpy.PointGeometry):
            point = location.firstPoint
            lon, lat = point.X, point.Y
        else:
            lon, lat = location

        try:
            fc = _api_request(
                "/search/coordinates",
                params={"location": f"{lon},{lat}"},
            )
        except RuntimeError as e:
            arcpy.AddWarning(str(e))
            return None

        parsed = _parse_feature_collection(fc)
        if not parsed:
            return None

        lon, lat, legal_loc, province, survey_system, boundary = parsed

        return {
            "address": legal_loc,
            "province": province,
            "survey_system": survey_system,
        }


# ---------------------------------------------------------------------------
# ArcGIS Pro Geoprocessing Tool
# ---------------------------------------------------------------------------


class TownshipCanadaGeoprocessingTool:
    """ArcGIS Pro geoprocessing tool for batch conversion of legal land descriptions.

    Converts a table/feature class column of legal land descriptions into
    a point feature class with coordinates and boundary polygons.
    """

    def __init__(self):
        self.label = "Convert Legal Land Descriptions"
        self.description = (
            "Batch convert Canadian legal land descriptions to GPS coordinates "
            "using the Township Canada API."
        )
        self.category = "Township Canada"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define geoprocessing tool parameters."""
        # Input table
        param_input = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
        )

        # Location field
        param_field = arcpy.Parameter(
            displayName="Legal Description Field",
            name="location_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
        )
        param_field.parameterDependencies = [param_input.name]

        # Output feature class
        param_output = arcpy.Parameter(
            displayName="Output Feature Class",
            name="output_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
        )

        # Include boundaries
        param_boundaries = arcpy.Parameter(
            displayName="Include Boundary Polygons",
            name="include_boundaries",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        param_boundaries.value = False

        return [param_input, param_field, param_output, param_boundaries]

    def execute(self, parameters, messages):
        """Execute the batch conversion."""
        input_table = parameters[0].valueAsText
        location_field = parameters[1].valueAsText
        output_fc = parameters[2].valueAsText
        include_boundaries = parameters[3].value

        sr = arcpy.SpatialReference(4326)

        # Create output feature class
        out_path = os.path.dirname(output_fc)
        out_name = os.path.basename(output_fc)
        arcpy.management.CreateFeatureclass(
            out_path, out_name, "POINT", spatial_reference=sr
        )

        # Add fields
        arcpy.management.AddField(output_fc, "LegalLocation", "TEXT", field_length=100)
        arcpy.management.AddField(output_fc, "Province", "TEXT", field_length=50)
        arcpy.management.AddField(output_fc, "SurveySystem", "TEXT", field_length=20)
        arcpy.management.AddField(output_fc, "Latitude", "DOUBLE")
        arcpy.management.AddField(output_fc, "Longitude", "DOUBLE")
        arcpy.management.AddField(output_fc, "Status", "TEXT", field_length=20)

        # Optional boundary polygon feature class
        boundary_fc = None
        if include_boundaries:
            boundary_fc = output_fc + "_boundaries"
            arcpy.management.CreateFeatureclass(
                out_path,
                os.path.basename(boundary_fc),
                "POLYGON",
                spatial_reference=sr,
            )
            arcpy.management.AddField(boundary_fc, "LegalLocation", "TEXT", field_length=100)

        # Count rows for progress
        row_count = int(arcpy.management.GetCount(input_table)[0])
        arcpy.SetProgressor("step", "Converting legal land descriptions...", 0, row_count, 1)

        # Process each row
        success_count = 0
        fail_count = 0

        fields = [location_field]
        insert_fields = ["SHAPE@", "LegalLocation", "Province", "SurveySystem", "Latitude", "Longitude", "Status"]

        with arcpy.da.InsertCursor(output_fc, insert_fields) as insert_cursor:
            boundary_cursor = None
            if boundary_fc:
                boundary_cursor = arcpy.da.InsertCursor(
                    boundary_fc, ["SHAPE@", "LegalLocation"]
                )

            try:
                with arcpy.da.SearchCursor(input_table, fields) as search_cursor:
                    for row in search_cursor:
                        location = str(row[0]).strip() if row[0] else ""
                        arcpy.SetProgressorLabel(f"Converting: {location}")

                        if not location:
                            fail_count += 1
                            arcpy.SetProgressorPosition()
                            continue

                        try:
                            fc = _api_request(
                                "/search/legal-location",
                                params={"location": location},
                            )
                            parsed = _parse_feature_collection(fc)

                            if parsed:
                                lon, lat, legal_loc, province, survey_system, boundary = parsed
                                point = arcpy.PointGeometry(
                                    arcpy.Point(lon, lat), sr
                                )
                                insert_cursor.insertRow([
                                    point, legal_loc, province, survey_system,
                                    lat, lon, "Success",
                                ])
                                success_count += 1

                                # Add boundary polygon if available
                                if boundary_cursor and boundary:
                                    try:
                                        geom = arcpy.AsShape(boundary, True)
                                        boundary_cursor.insertRow([geom, legal_loc])
                                    except Exception:
                                        pass  # Skip invalid boundaries
                            else:
                                fail_count += 1

                        except RuntimeError as e:
                            messages.addWarningMessage(f"Failed to convert '{location}': {e}")
                            fail_count += 1

                        arcpy.SetProgressorPosition()
            finally:
                if boundary_cursor:
                    del boundary_cursor

        messages.addMessage(
            f"Conversion complete: {success_count} succeeded, {fail_count} failed "
            f"out of {row_count} total."
        )

        return output_fc


# ---------------------------------------------------------------------------
# Configuration Tool
# ---------------------------------------------------------------------------


class ConfigureAPIKey:
    """Geoprocessing tool to configure the Township Canada API key."""

    def __init__(self):
        self.label = "Configure API Key"
        self.description = "Set your Township Canada API key for use with the locator and tools."
        self.category = "Township Canada"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_key = arcpy.Parameter(
            displayName="API Key",
            name="api_key",
            datatype="GPStringHidden",
            parameterType="Required",
            direction="Input",
        )
        return [param_key]

    def execute(self, parameters, messages):
        api_key = parameters[0].valueAsText

        config_dir = os.path.join(os.path.expanduser("~"), ".townshipcanada")
        os.makedirs(config_dir, exist_ok=True)

        config_path = os.path.join(config_dir, "config.json")
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)

        config["api_key"] = api_key

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Validate the key
        try:
            _api_request(
                "/search/legal-location",
                params={"location": "NW-36-42-3-W5"},
            )
            messages.addMessage("API key configured and validated successfully.")
        except RuntimeError as e:
            messages.addWarningMessage(f"API key saved but validation failed: {e}")

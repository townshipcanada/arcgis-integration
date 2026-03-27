"""
Township Canada Locator for ArcGIS Pro.

A custom geocoding locator role that converts Canadian legal land descriptions
(DLS, NTS, Geographic Townships) to GPS coordinates using the Township Canada SDK.

Integrates with ArcGIS Pro's Locate pane so users can search by legal land
description directly from the search bar.

Requirements:
    - ArcGIS Pro 3.2+ (tested up to 3.7)
    - Python 3.9+ (bundled with ArcGIS Pro)
    - townshipcanada Python SDK (pip install townshipcanada)
    - Township Canada API key (https://townshipcanada.com/developers)
"""

import json
import logging
import os
import re
import time

import arcpy
from townshipcanada import (
    TownshipCanada,
    NotFoundError,
    RateLimitError,
    AuthenticationError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

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


def _get_township_canada_api_key():
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


def _get_client():
    """Create and return a TownshipCanada SDK client.

    Returns:
        TownshipCanada: Configured SDK client.

    Raises:
        RuntimeError: If no API key is configured.
    """
    api_key = _get_township_canada_api_key()
    if not api_key:
        raise RuntimeError(
            "Township Canada API key not configured. "
            "Set the TOWNSHIP_CANADA_API_KEY environment variable or run "
            "the configuration tool."
        )
    return TownshipCanada(api_key)


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
            client = _get_client()
            search_result = client.search(location)
        except (RuntimeError, AuthenticationError) as e:
            arcpy.AddWarning(str(e))
            return []
        except NotFoundError:
            return []

        result = {
            "address": search_result.legal_location,
            "location": arcpy.PointGeometry(
                arcpy.Point(search_result.longitude, search_result.latitude),
                arcpy.SpatialReference(4326),
            ),
            "score": 100,
            "attributes": {
                "LegalLocation": search_result.legal_location,
                "Province": search_result.province,
                "SurveySystem": search_result.survey_system,
                "Latitude": search_result.latitude,
                "Longitude": search_result.longitude,
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
            client = _get_client()
            suggestions = client.autocomplete(text, limit=min(max_suggestions, 10))
        except (RuntimeError, AuthenticationError, NotFoundError):
            return []

        return [
            {
                "text": s.legal_location,
                "isCollection": False,
            }
            for s in suggestions
            if s.legal_location
        ]

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
            client = _get_client()
            search_result = client.reverse(lon, lat)
        except (RuntimeError, AuthenticationError) as e:
            arcpy.AddWarning(str(e))
            return None
        except NotFoundError:
            return None

        return {
            "address": search_result.legal_location,
            "province": search_result.province,
            "survey_system": search_result.survey_system,
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

        # Collect all locations from the input table
        row_count = int(arcpy.management.GetCount(input_table)[0])
        arcpy.SetProgressor("step", "Converting legal land descriptions...", 0, row_count, 1)

        locations = []
        fields = [location_field]
        with arcpy.da.SearchCursor(input_table, fields) as search_cursor:
            for row in search_cursor:
                loc = str(row[0]).strip() if row[0] else ""
                locations.append(loc)

        # Batch search using the SDK
        client = _get_client()
        valid_locations = [loc for loc in locations if loc]

        batch_result = None
        if valid_locations:
            # Retry loop for rate limiting during batch
            for attempt in range(4):
                try:
                    batch_result = client.batch_search(valid_locations, chunk_size=100)
                    break
                except RateLimitError as e:
                    if attempt < 3:
                        wait = e.retry_after if e.retry_after else 2 ** attempt
                        logger.info(
                            "Rate limited during batch search, retrying in %ds (attempt %d/3)",
                            wait, attempt + 1,
                        )
                        time.sleep(wait)
                    else:
                        raise RuntimeError(
                            f"Rate limited after {attempt + 1} attempts: {e}"
                        ) from e
                except AuthenticationError as e:
                    raise RuntimeError(f"Authentication failed: {e}") from e

        # Build a lookup from normalized legal location to SearchResult.
        # batch_search only returns successful items, so match by legal_location.
        result_map = {}
        if batch_result:
            for sr in batch_result.results:
                # Index by normalized form for case-insensitive matching
                result_map[sr.legal_location.strip().lower()] = sr

        # Write results
        success_count = 0
        fail_count = 0
        insert_fields = ["SHAPE@", "LegalLocation", "Province", "SurveySystem", "Latitude", "Longitude", "Status"]

        with arcpy.da.InsertCursor(output_fc, insert_fields) as insert_cursor:
            boundary_cursor = None
            if boundary_fc:
                boundary_cursor = arcpy.da.InsertCursor(
                    boundary_fc, ["SHAPE@", "LegalLocation"]
                )

            try:
                for loc in locations:
                    arcpy.SetProgressorLabel(f"Processing: {loc}")

                    if not loc:
                        fail_count += 1
                        arcpy.SetProgressorPosition()
                        continue

                    search_result = result_map.get(loc.strip().lower())
                    if search_result:
                        point = arcpy.PointGeometry(
                            arcpy.Point(search_result.longitude, search_result.latitude), sr
                        )
                        insert_cursor.insertRow([
                            point,
                            search_result.legal_location,
                            search_result.province,
                            search_result.survey_system,
                            search_result.latitude,
                            search_result.longitude,
                            "Success",
                        ])
                        success_count += 1

                        # Add boundary polygon if available
                        if boundary_cursor and search_result.boundary:
                            try:
                                boundary_geojson = search_result.boundary.model_dump()
                                geom = arcpy.AsShape(boundary_geojson, True)
                                boundary_cursor.insertRow([geom, search_result.legal_location])
                            except Exception as e:
                                logger.warning(
                                    "Skipping invalid boundary geometry for '%s': %s",
                                    search_result.legal_location, e,
                                )
                    else:
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

        # Validate the key with a test search
        try:
            client = TownshipCanada(api_key)
            client.search("NW-36-42-3-W5")
            messages.addMessage("API key configured and validated successfully.")
        except AuthenticationError:
            messages.addWarningMessage("API key saved but validation failed: invalid API key.")
        except Exception as e:
            messages.addWarningMessage(f"API key saved but validation failed: {e}")

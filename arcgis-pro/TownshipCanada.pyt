"""
Township Canada Python Toolbox for ArcGIS Pro.

This toolbox provides geoprocessing tools for converting Canadian legal land
descriptions (DLS, NTS, Geographic Townships) to GPS coordinates using the
Township Canada API.

Installation:
    1. Copy this folder to a location on your machine.
    2. In ArcGIS Pro, open the Catalog pane.
    3. Right-click "Toolboxes" > "Add Toolbox" and select this .pyt file.
    4. Run "Configure API Key" first to set your Township Canada API key.

Tools:
    - Configure API Key: Set your Township Canada API key
    - Convert Legal Land Descriptions: Batch convert a table of descriptions
    - Search Legal Land Description: Convert a single description
"""

import arcpy
from township_canada_locator import (
    ConfigureAPIKey,
    TownshipCanadaGeoprocessingTool,
    TownshipCanadaLocator,
    _township_canada_api_request,
    _parse_township_canada_feature_collection,
)


class Toolbox:
    def __init__(self):
        self.label = "Township Canada"
        self.alias = "townshipcanada"
        self.tools = [
            TownshipCanadaConfigureAPIKeyTool,
            TownshipCanadaBatchConvertTool,
            TownshipCanadaSearchTool,
        ]


class TownshipCanadaConfigureAPIKeyTool(ConfigureAPIKey):
    """Wrapper for the ConfigureAPIKey tool."""
    pass


class TownshipCanadaBatchConvertTool(TownshipCanadaGeoprocessingTool):
    """Wrapper for the batch conversion tool."""
    pass


class TownshipCanadaSearchTool:
    """Search for a single legal land description and add the result to the map."""

    def __init__(self):
        self.label = "Search Legal Land Description"
        self.description = (
            "Convert a single Canadian legal land description to GPS coordinates "
            "and optionally add the result to the current map."
        )
        self.category = "Township Canada"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_location = arcpy.Parameter(
            displayName="Legal Land Description",
            name="location",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param_location.filter.type = "ValueList"
        param_location.filter.list = []

        param_add_to_map = arcpy.Parameter(
            displayName="Add Result to Map",
            name="add_to_map",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        param_add_to_map.value = True

        param_output = arcpy.Parameter(
            displayName="Result",
            name="result",
            datatype="GPString",
            parameterType="Derived",
            direction="Output",
        )

        return [param_location, param_add_to_map, param_output]

    def updateParameters(self, parameters):
        """Provide autocomplete suggestions as the user types."""
        location = parameters[0].valueAsText
        if location and len(location) >= 2:
            locator = TownshipCanadaLocator()
            suggestions = locator.suggest(location)
            parameters[0].filter.list = [s["text"] for s in suggestions]

    def execute(self, parameters, messages):
        location = parameters[0].valueAsText
        add_to_map = parameters[1].value

        locator = TownshipCanadaLocator()
        results = locator.geocode(location)

        if not results:
            messages.addErrorMessage(f"No results found for: {location}")
            return

        result = results[0]
        attrs = result["attributes"]

        messages.addMessage(f"Legal Location: {attrs['LegalLocation']}")
        messages.addMessage(f"Province: {attrs['Province']}")
        messages.addMessage(f"Survey System: {attrs['SurveySystem']}")
        messages.addMessage(f"Latitude: {attrs['Latitude']:.6f}")
        messages.addMessage(f"Longitude: {attrs['Longitude']:.6f}")

        parameters[2].value = (
            f"{attrs['LegalLocation']} ({attrs['Latitude']:.6f}, {attrs['Longitude']:.6f})"
        )

        if add_to_map:
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                active_map = aprx.activeMap
                if active_map:
                    # Create an in-memory feature class for the result
                    sr = arcpy.SpatialReference(4326)
                    mem_fc = "memory/township_result"
                    if arcpy.Exists(mem_fc):
                        arcpy.management.Delete(mem_fc)
                    arcpy.management.CreateFeatureclass(
                        "memory", "township_result", "POINT", spatial_reference=sr
                    )
                    arcpy.management.AddField(mem_fc, "LegalLocation", "TEXT", field_length=100)
                    arcpy.management.AddField(mem_fc, "Province", "TEXT", field_length=50)

                    with arcpy.da.InsertCursor(mem_fc, ["SHAPE@", "LegalLocation", "Province"]) as cursor:
                        cursor.insertRow([
                            result["location"],
                            attrs["LegalLocation"],
                            attrs["Province"],
                        ])

                    active_map.addDataFromPath(mem_fc)
                    messages.addMessage("Result added to the active map.")
            except Exception as e:
                messages.addWarningMessage(f"Could not add to map: {e}")

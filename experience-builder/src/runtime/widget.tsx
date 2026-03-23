/** @jsx jsx */
import {
  jsx,
  type AllWidgetProps,
  type DataSource,
  React,
  css
} from 'jimu-core'
import { JimuMapViewComponent, type JimuMapView } from 'jimu-arcgis'
import { TextInput, Button, Loading, Alert, Label, Switch } from 'jimu-ui'
import { SearchOutlined } from 'jimu-icons/outlined/editor/search'
import { PinEsriOutlined } from 'jimu-icons/outlined/gis/pin-esri'
import { type IMConfig, TRIAL_API_BASE_URL, PAID_API_BASE_URL } from '../config'
import Graphic from 'esri/Graphic'
import Point from 'esri/geometry/Point'
import Polygon from 'esri/geometry/Polygon'
import SimpleFillSymbol from 'esri/symbols/SimpleFillSymbol'
import SimpleMarkerSymbol from 'esri/symbols/SimpleMarkerSymbol'
import GraphicsLayer from 'esri/layers/GraphicsLayer'

interface TownshipCanadaSearchResult {
  legalLocation: string
  latitude: number
  longitude: number
  province: string
  surveySystem: string
  boundary: any | null
}

interface TownshipCanadaWidgetState {
  query: string
  result: TownshipCanadaSearchResult | null
  suggestions: string[]
  isLoading: boolean
  error: string | null
  reverseMode: boolean
}

const style = css`
  .township-canada-widget {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .township-canada-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e5e7eb;
  }

  .township-canada-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #1a3d2e;
  }

  .township-canada-search-form {
    display: flex;
    gap: 8px;
  }

  .township-canada-search-form .search-input {
    flex: 1;
  }

  .township-canada-suggestions {
    list-style: none;
    margin: 0;
    padding: 0;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    max-height: 150px;
    overflow-y: auto;
  }

  .township-canada-suggestions li {
    padding: 8px 12px;
    cursor: pointer;
    font-size: 13px;
    font-family: 'Consolas', 'Monaco', monospace;
  }

  .township-canada-suggestions li:hover {
    background: #f0fdf4;
  }

  .township-canada-result {
    border: 1px solid #d1fae5;
    border-radius: 8px;
    padding: 12px;
    background: #f0fdf4;
  }

  .township-canada-result h4 {
    margin: 0 0 8px 0;
    font-size: 15px;
    font-weight: 600;
    color: #1a3d2e;
    font-family: 'Consolas', 'Monaco', monospace;
  }

  .township-canada-result-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 8px;
  }

  .township-canada-result-item {
    background: white;
    border-radius: 6px;
    padding: 8px;
  }

  .township-canada-result-item .label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #6b7280;
    margin-bottom: 2px;
  }

  .township-canada-result-item .value {
    font-size: 13px;
    font-weight: 500;
    color: #1f2937;
    font-family: 'Consolas', 'Monaco', monospace;
  }

  .township-canada-reverse-hint {
    font-size: 12px;
    color: #6b7280;
    text-align: center;
    padding: 8px;
    background: #fef3c7;
    border-radius: 6px;
  }

  .township-canada-footer {
    font-size: 11px;
    color: #9ca3af;
    text-align: center;
    padding-top: 8px;
    border-top: 1px solid #e5e7eb;
  }

  .township-canada-footer a {
    color: #4a7c59;
    text-decoration: none;
  }
`

export default class TownshipCanadaWidget extends React.PureComponent<
  AllWidgetProps<IMConfig>,
  TownshipCanadaWidgetState
> {
  private jimuMapView: JimuMapView | null = null
  private graphicsLayer: __esri.GraphicsLayer | null = null
  private debounceTimer: any = null
  private mapClickHandler: any = null

  constructor (props: AllWidgetProps<IMConfig>) {
    super(props)
    this.state = {
      query: '',
      result: null,
      suggestions: [],
      isLoading: false,
      error: null,
      reverseMode: false
    }
  }

  componentWillUnmount (): void {
    if (this.mapClickHandler) {
      this.mapClickHandler.remove()
      this.mapClickHandler = null
    }
  }

  private getApiBaseUrl (): string {
    const isTrialKey = this.props.config?.isTrialKey ?? true
    return isTrialKey ? TRIAL_API_BASE_URL : PAID_API_BASE_URL
  }

  private async apiRequest (endpoint: string, params: Record<string, string>): Promise<any> {
    const apiKey = this.props.config?.apiKey
    if (!apiKey) {
      throw new Error('API key not configured. Open widget settings to add your Township Canada API key.')
    }

    const baseUrl = this.getApiBaseUrl()
    const url = new URL(baseUrl + endpoint)
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value)
    })

    const response = await fetch(url.toString(), {
      headers: {
        'X-API-Key': apiKey,
        Accept: 'application/json',
        'User-Agent': 'townshipcanada-experience-builder/1.0.0'
      }
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`API error (${response.status}): ${body}`)
    }

    return response.json()
  }

  private parseFeatureCollection (fc: any): TownshipCanadaSearchResult | null {
    const features = fc?.features || []
    const centroid = features.find((f: any) => f.properties?.shape === 'centroid')
    const grid = features.find((f: any) => f.properties?.shape === 'grid')

    if (!centroid?.geometry?.coordinates) return null

    const [lng, lat] = centroid.geometry.coordinates
    const props = centroid.properties || {}

    return {
      legalLocation: props.legal_location || '',
      latitude: lat,
      longitude: lng,
      province: props.province || '',
      surveySystem: props.survey_system || '',
      boundary: grid?.geometry || null
    }
  }

  private handleSearch = async (): Promise<void> => {
    const { query } = this.state
    if (!query.trim()) return

    this.setState({ isLoading: true, error: null, suggestions: [] })

    try {
      const fc = await this.apiRequest('/search/legal-location', { location: query })
      const result = this.parseFeatureCollection(fc)

      if (!result) {
        this.setState({ error: `No results found for "${query}"`, isLoading: false })
        return
      }

      this.setState({ result, isLoading: false })
      this.plotResult(result)
    } catch (e: any) {
      this.setState({ error: e.message, isLoading: false })
    }
  }

  private handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const query = e.target.value
    this.setState({ query })

    // Debounced autocomplete
    if (this.debounceTimer) clearTimeout(this.debounceTimer)
    if (query.length >= 2) {
      this.debounceTimer = setTimeout(() => this.fetchSuggestions(query), 300)
    } else {
      this.setState({ suggestions: [] })
    }
  }

  private handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter') {
      this.handleSearch()
    }
  }

  private async fetchSuggestions (query: string): Promise<void> {
    try {
      const fc = await this.apiRequest('/autocomplete/legal-location', {
        location: query,
        limit: '5'
      })
      const suggestions = (fc?.features || [])
        .map((f: any) => f.properties?.legal_location)
        .filter(Boolean)
      this.setState({ suggestions })
    } catch (err: any) {
      console.error('Township Canada autocomplete error:', err.message)
    }
  }

  private handleSuggestionClick = (suggestion: string): void => {
    this.setState({ query: suggestion, suggestions: [] }, () => {
      this.handleSearch()
    })
  }

  private plotResult (result: TownshipCanadaSearchResult): void {
    if (!this.jimuMapView?.view) return

    const view = this.jimuMapView.view

    // Clear previous graphics
    if (this.graphicsLayer) {
      this.graphicsLayer.removeAll()
    } else {
      this.graphicsLayer = new GraphicsLayer({ title: 'Township Canada Results' })
      view.map.add(this.graphicsLayer)
    }

    // Add point marker
    const point = new Point({
      longitude: result.longitude,
      latitude: result.latitude,
      spatialReference: { wkid: 4326 }
    })

    const markerSymbol = new SimpleMarkerSymbol({
      color: [196, 93, 58], // #c45d3a (accent)
      size: 12,
      outline: { color: [255, 255, 255], width: 2 }
    })

    this.graphicsLayer.add(
      new Graphic({
        geometry: point,
        symbol: markerSymbol,
        attributes: {
          LegalLocation: result.legalLocation,
          Province: result.province,
          SurveySystem: result.surveySystem
        },
        popupTemplate: {
          title: '{LegalLocation}',
          content: '{Province} — {SurveySystem}'
        }
      })
    )

    // Add boundary polygon if enabled
    if (this.props.config?.showBoundaries && result.boundary) {
      try {
        const rings =
          result.boundary.type === 'MultiPolygon'
            ? result.boundary.coordinates.flat()
            : result.boundary.coordinates

        const polygon = new Polygon({
          rings,
          spatialReference: { wkid: 4326 }
        })

        const fillSymbol = new SimpleFillSymbol({
          color: [74, 124, 89, 40], // #4a7c59 (sage) at 15% opacity
          outline: { color: [74, 124, 89, 200], width: 2 }
        })

        this.graphicsLayer.add(new Graphic({ geometry: polygon, symbol: fillSymbol }))
      } catch (err: any) {
        console.error('Township Canada boundary rendering error:', err.message)
      }
    }

    // Zoom to result
    if (this.props.config?.zoomToResult) {
      view.goTo({
        center: [result.longitude, result.latitude],
        zoom: this.props.config?.zoomLevel || 14
      })
    }
  }

  private handleMapViewReady = (jimuMapView: JimuMapView): void => {
    this.jimuMapView = jimuMapView
  }

  private toggleReverseMode = (): void => {
    const reverseMode = !this.state.reverseMode
    this.setState({ reverseMode })

    if (reverseMode && this.jimuMapView?.view) {
      this.mapClickHandler = this.jimuMapView.view.on('click', this.handleMapClick)
    } else if (this.mapClickHandler) {
      this.mapClickHandler.remove()
      this.mapClickHandler = null
    }
  }

  private handleMapClick = async (event: any): Promise<void> => {
    if (!this.state.reverseMode) return

    const { mapPoint } = event
    if (!mapPoint) return

    const lon = mapPoint.longitude
    const lat = mapPoint.latitude

    this.setState({ isLoading: true, error: null })

    try {
      const fc = await this.apiRequest('/search/coordinates', {
        location: `${lon},${lat}`
      })
      const result = this.parseFeatureCollection(fc)

      if (!result) {
        this.setState({ error: 'No legal land description found at this location.', isLoading: false })
        return
      }

      this.setState({ result, query: result.legalLocation, isLoading: false })
      this.plotResult(result)
    } catch (e: any) {
      this.setState({ error: e.message, isLoading: false })
    }
  }

  render (): React.ReactNode {
    const { query, result, suggestions, isLoading, error, reverseMode } = this.state
    const config = this.props.config

    return (
      <div className="township-canada-widget" css={style}>
        <div className="township-canada-header">
          <PinEsriOutlined size="m" />
          <h3>Township Canada</h3>
        </div>

        {/* Search form */}
        <div className="township-canada-search-form">
          <TextInput
            className="search-input"
            placeholder="e.g. NW-36-42-3-W5"
            value={query}
            onChange={this.handleInputChange}
            onKeyDown={this.handleKeyDown}
            disabled={isLoading}
          />
          <Button
            type="primary"
            onClick={this.handleSearch}
            disabled={isLoading || !query.trim()}
            icon
          >
            <SearchOutlined />
          </Button>
        </div>

        {/* Autocomplete suggestions */}
        {suggestions.length > 0 && (
          <ul className="township-canada-suggestions">
            {suggestions.map((s) => (
              <li key={s} onClick={() => this.handleSuggestionClick(s)}>
                {s}
              </li>
            ))}
          </ul>
        )}

        {/* Reverse geocode toggle */}
        {config?.enableReverseGeocode && (
          <Label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <Switch checked={reverseMode} onChange={this.toggleReverseMode} />
            Click map to find legal description
          </Label>
        )}

        {reverseMode && (
          <div className="township-canada-reverse-hint">
            Click anywhere on the map to find the legal land description at that location.
          </div>
        )}

        {/* Loading */}
        {isLoading && <Loading type="SECONDARY" />}

        {/* Error */}
        {error && <Alert type="warning" text={error} closable onClose={() => this.setState({ error: null })} />}

        {/* Result */}
        {result && !isLoading && (
          <div className="township-canada-result">
            <h4>{result.legalLocation}</h4>
            <div className="township-canada-result-grid">
              <div className="township-canada-result-item">
                <div className="label">Latitude</div>
                <div className="value">{result.latitude.toFixed(6)}</div>
              </div>
              <div className="township-canada-result-item">
                <div className="label">Longitude</div>
                <div className="value">{result.longitude.toFixed(6)}</div>
              </div>
              <div className="township-canada-result-item">
                <div className="label">Province</div>
                <div className="value">{result.province}</div>
              </div>
              <div className="township-canada-result-item">
                <div className="label">Survey System</div>
                <div className="value">{result.surveySystem}</div>
              </div>
            </div>
          </div>
        )}

        {/* Map view binding */}
        {this.props.useMapWidgetIds?.length > 0 && (
          <JimuMapViewComponent
            useMapWidgetId={this.props.useMapWidgetIds[0]}
            onActiveViewChange={this.handleMapViewReady}
          />
        )}

        <div className="township-canada-footer">
          Powered by <a href="https://townshipcanada.com" target="_blank" rel="noopener noreferrer">Township Canada</a>
        </div>
      </div>
    )
  }
}

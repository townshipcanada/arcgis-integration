/** @jsx jsx */
import { jsx, React, type IMState } from 'jimu-core'
import { type AllWidgetSettingProps } from 'jimu-for-builder'
import {
  TextInput,
  Switch,
  Label,
  NumericInput,
  Alert
} from 'jimu-ui'
import { MapWidgetSelector } from 'jimu-ui/advanced/setting-components'
import { type IMConfig, defaultConfig } from '../config'

export default class Setting extends React.PureComponent<
  AllWidgetSettingProps<IMConfig>
> {
  private onApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    this.props.onSettingChange({
      id: this.props.id,
      config: this.props.config.set('apiKey', e.target.value)
    })
  }

  private onIsTrialKeyChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    this.props.onSettingChange({
      id: this.props.id,
      config: this.props.config.set('isTrialKey', e.target.checked)
    })
  }

  private onShowBoundariesChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    this.props.onSettingChange({
      id: this.props.id,
      config: this.props.config.set('showBoundaries', e.target.checked)
    })
  }

  private onZoomToResultChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    this.props.onSettingChange({
      id: this.props.id,
      config: this.props.config.set('zoomToResult', e.target.checked)
    })
  }

  private onZoomLevelChange = (value: number): void => {
    this.props.onSettingChange({
      id: this.props.id,
      config: this.props.config.set('zoomLevel', value)
    })
  }

  private onEnableReverseGeocodeChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    this.props.onSettingChange({
      id: this.props.id,
      config: this.props.config.set('enableReverseGeocode', e.target.checked)
    })
  }

  private onMapWidgetSelected = (useMapWidgetIds: string[]): void => {
    this.props.onSettingChange({
      id: this.props.id,
      useMapWidgetIds
    })
  }

  render (): React.ReactNode {
    const config = this.props.config || defaultConfig
    const hasApiKey = !!config.apiKey

    return (
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <h4 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Township Canada Settings</h4>

        {/* API Key */}
        <div>
          <Label style={{ fontWeight: 500, marginBottom: 4, display: 'block' }}>
            API Key
          </Label>
          <TextInput
            type="password"
            placeholder="tc_xxxxxxxxxxxxxxxx"
            value={config.apiKey || ''}
            onChange={this.onApiKeyChange}
          />
          <p style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>
            Get your API key at{' '}
            <a href="https://townshipcanada.com/developers" target="_blank" rel="noopener noreferrer">
              townshipcanada.com/developers
            </a>
          </p>
          {!hasApiKey && (
            <Alert
              type="warning"
              text="An API key is required for the widget to function."
              style={{ marginTop: 8 }}
            />
          )}
        </div>

        {/* Trial key toggle */}
        <Label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Switch
            checked={config.isTrialKey ?? defaultConfig.isTrialKey}
            onChange={this.onIsTrialKeyChange}
          />
          Using a trial API key
        </Label>
        <p style={{ fontSize: 11, color: '#6b7280', marginTop: -8 }}>
          Enable this if you are using a free trial key. Trial keys use a different API endpoint.
        </p>

        {/* Map Widget */}
        <div>
          <Label style={{ fontWeight: 500, marginBottom: 4, display: 'block' }}>
            Connected Map
          </Label>
          <MapWidgetSelector
            useMapWidgetIds={this.props.useMapWidgetIds}
            onSelect={this.onMapWidgetSelected}
          />
        </div>

        {/* Show boundaries */}
        <Label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Switch
            checked={config.showBoundaries ?? defaultConfig.showBoundaries}
            onChange={this.onShowBoundariesChange}
          />
          Show boundary polygons
        </Label>

        {/* Zoom to result */}
        <Label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Switch
            checked={config.zoomToResult ?? defaultConfig.zoomToResult}
            onChange={this.onZoomToResultChange}
          />
          Zoom to result
        </Label>

        {/* Zoom level */}
        {config.zoomToResult && (
          <div>
            <Label style={{ fontWeight: 500, marginBottom: 4, display: 'block' }}>
              Zoom Level
            </Label>
            <NumericInput
              min={1}
              max={20}
              value={config.zoomLevel ?? defaultConfig.zoomLevel}
              onChange={this.onZoomLevelChange}
            />
          </div>
        )}

        {/* Reverse geocode */}
        <Label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Switch
            checked={config.enableReverseGeocode ?? defaultConfig.enableReverseGeocode}
            onChange={this.onEnableReverseGeocodeChange}
          />
          Enable reverse geocode (click map)
        </Label>
      </div>
    )
  }
}

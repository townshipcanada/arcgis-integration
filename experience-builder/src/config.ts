import { type ImmutableObject } from 'jimu-core'

export interface Config {
  /**
   * Township Canada API key (trial or paid). Required for all API calls.
   * Get a trial key at https://townshipcanada.com/api/try?ref=arcgis-exb
   * or a paid key at https://townshipcanada.com/developers
   */
  apiKey: string

  /**
   * Whether the configured API key is a trial key.
   * Trial keys use a different API endpoint than paid keys.
   */
  isTrialKey: boolean

  /**
   * Whether to show boundary polygons on the map when a result is found.
   */
  showBoundaries: boolean

  /**
   * Whether to zoom the map to the result location.
   */
  zoomToResult: boolean

  /**
   * Default zoom level when flying to a result (1-20).
   */
  zoomLevel: number

  /**
   * Whether to show the reverse geocode button (click map to find LLD).
   */
  enableReverseGeocode: boolean
}

export type IMConfig = ImmutableObject<Config>

/**
 * API base URL for trial keys.
 * Trial keys must use the integration trial endpoint.
 */
export const TRIAL_API_BASE_URL = 'https://townshipcanada.com/api/integrations/trial'

/**
 * API base URL for paid keys.
 * Paid keys use the developer API directly.
 */
export const PAID_API_BASE_URL = 'https://developer.townshipcanada.com'

/**
 * URL where users can obtain a free trial API key.
 */
export const TRIAL_URL = 'https://townshipcanada.com/api/try?ref=arcgis-exb'

export const defaultConfig: Config = {
  apiKey: '',
  isTrialKey: true,
  showBoundaries: true,
  zoomToResult: true,
  zoomLevel: 14,
  enableReverseGeocode: true
}

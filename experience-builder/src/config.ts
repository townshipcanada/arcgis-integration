import { type ImmutableObject } from 'jimu-core'

export interface Config {
  /**
   * Township Canada API key. Required for all API calls.
   * Get a key at https://townshipcanada.com/developers
   */
  apiKey: string

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
 * API base URL for the Township Canada developer API.
 */
export const API_BASE_URL = 'https://developer.townshipcanada.com'

export const defaultConfig: Config = {
  apiKey: '',
  showBoundaries: true,
  zoomToResult: true,
  zoomLevel: 14,
  enableReverseGeocode: true
}

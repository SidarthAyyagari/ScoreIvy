const DEFAULT_API_PORT = '8000'

function stripTrailingSlash(url: string): string {
  return url.replace(/\/$/, '')
}

/**
 * Resolve backend base URL for browser requests.
 * When the UI is opened via LAN IP (e.g. phone at 10.0.0.174:3001) but
 * NEXT_PUBLIC_API_URL is still localhost, use the same host as the page on port 8000.
 */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim()

  if (typeof window === 'undefined') {
    return configured ? stripTrailingSlash(configured) : `http://localhost:${DEFAULT_API_PORT}`
  }

  const pageHost = window.location.hostname
  const pageIsLocal = pageHost === 'localhost' || pageHost === '127.0.0.1'

  if (configured) {
    try {
      const apiUrl = new URL(configured)
      const apiHost = apiUrl.hostname
      const apiIsLocal = apiHost === 'localhost' || apiHost === '127.0.0.1'

      if (apiIsLocal && !pageIsLocal) {
        const port = apiUrl.port || DEFAULT_API_PORT
        return stripTrailingSlash(`${window.location.protocol}//${pageHost}:${port}`)
      }

      return stripTrailingSlash(configured)
    } catch {
      /* ignore invalid URL */
    }
  }

  if (!pageIsLocal) {
    return `${window.location.protocol}//${pageHost}:${DEFAULT_API_PORT}`
  }

  return `http://localhost:${DEFAULT_API_PORT}`
}

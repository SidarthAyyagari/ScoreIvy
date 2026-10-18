import { getApiBaseUrl } from '../lib/apiBaseUrl'

export class ApiError extends Error {
  constructor(message: string, public status: number, public body: unknown) {
    super(message)
  }
}

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null

  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const headers: HeadersInit = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers,
  }

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
    const detail = error.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(', ')
          : 'Request failed'
    throw new ApiError(message, response.status, error)
  }

  return response
}

/** Fetch an authenticated file and save it via the browser. */
export async function apiDownload(endpoint: string, fallbackName: string): Promise<void> {
  const response = await apiRequest(endpoint)
  const disposition = response.headers.get('Content-Disposition') || ''
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] || fallbackName
  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export async function apiJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await apiRequest(endpoint, options)
  if (response.status === 204) {
    return undefined as T
  }
  return response.json()
}

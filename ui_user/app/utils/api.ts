import { getApiBaseUrl } from '../lib/apiBaseUrl'

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
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
    throw new Error(message)
  }

  return response
}

export async function apiJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await apiRequest(endpoint, options)
  if (response.status === 204) {
    return undefined as T
  }
  return response.json()
}

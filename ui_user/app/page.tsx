'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from './contexts/AuthContext'
import { apiJson } from './utils/api'
import { getApiBaseUrl } from './lib/apiBaseUrl'
import styles from './page.module.css'

type LoginUser = {
  id: number
  email: string
  name: string | null
  picture: string | null
  is_admin: boolean
}

type LoginResponse = {
  access_token: string
  user: LoginUser
}

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  const [error, setError] = useState('')
  const [devLoginAvailable, setDevLoginAvailable] = useState(false)
  const [devLoginLoading, setDevLoginLoading] = useState(false)

  useEffect(() => {
    fetch(`${getApiBaseUrl()}/api/health`)
      .then((res) => res.json())
      .then((data: { skip_admin_auth?: boolean }) => {
        setDevLoginAvailable(!!data.skip_admin_auth)
      })
      .catch(() => setDevLoginAvailable(false))
  }, [])

  const finishLogin = (response: LoginResponse) => {
    login(response.user, response.access_token)
    router.push('/dashboard')
  }

  const handleDevLogin = async () => {
    try {
      setError('')
      setDevLoginLoading(true)
      const response = await apiJson<LoginResponse>('/api/auth/dev-login', { method: 'POST' })
      finishLogin(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dev login failed')
    } finally {
      setDevLoginLoading(false)
    }
  }

  const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
    try {
      setError('')

      if (!credentialResponse.credential) {
        setError('No credential received from Google')
        return
      }

      const base64Url = credentialResponse.credential.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )

      const userInfo = JSON.parse(jsonPayload)

      const response = await apiJson<LoginResponse>('/api/auth/oauth-login', {
        method: 'POST',
        body: JSON.stringify({
          email: userInfo.email,
          name: userInfo.name,
          picture: userInfo.picture,
          oauth_provider: 'google',
          oauth_id: userInfo.sub,
        }),
      })

      finishLogin(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.')
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.loginCard}>
        <h1 className={styles.title}>ScoreIvy</h1>
        <p className={styles.subtitle}>
          {devLoginAvailable
            ? 'Dev mode: sign in without Google (LAN-friendly).'
            : 'Welcome! Sign in to continue.'}
        </p>

        {error && <div className={styles.error}>{error}</div>}

        {devLoginAvailable && (
          <>
            <button
              type="button"
              className={styles.devButton}
              onClick={handleDevLogin}
              disabled={devLoginLoading}
            >
              {devLoginLoading ? 'Signing in…' : 'Continue without Google (dev)'}
            </button>
            <p className={styles.divider}>or use Google</p>
          </>
        )}

        <div className={styles.oauthSection}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => setError('Google login failed. Please try again.')}
            useOneTap={!devLoginAvailable}
          />
        </div>
      </div>
    </div>
  )
}

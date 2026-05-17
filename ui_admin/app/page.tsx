'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from './contexts/AuthContext'
import { apiJson } from './utils/api'
import { isAdminGateEnabled } from './lib/config'
import styles from './page.module.css'

export default function LoginPage() {
  const { login, isAuthenticated, isAdmin, isLoading } = useAuth()
  const router = useRouter()
  const [error, setError] = useState('')

  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.search.includes('error=not_admin')) {
      setError('Your account is not an admin. Add your email to ADMIN_EMAILS in backend/.env')
    }
  }, [])

  const adminGateEnabled = isAdminGateEnabled()

  useEffect(() => {
    if (!isLoading && isAuthenticated && (isAdmin || !adminGateEnabled)) {
      router.replace('/dashboard')
    }
  }, [isLoading, isAuthenticated, isAdmin, adminGateEnabled, router])

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

      const response = await apiJson<{
        access_token: string
        user: {
          id: number
          email: string
          name: string | null
          picture: string | null
          is_admin: boolean
        }
      }>('/api/auth/oauth-login', {
        method: 'POST',
        body: JSON.stringify({
          email: userInfo.email,
          name: userInfo.name,
          picture: userInfo.picture,
          oauth_provider: 'google',
          oauth_id: userInfo.sub,
        }),
      })

      if (adminGateEnabled && !response.user.is_admin) {
        setError('Your account is not an admin. Add your email to ADMIN_EMAILS in backend/.env')
        return
      }

      login(response.user, response.access_token)
      router.push('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  if (isLoading) {
    return <div className={styles.container}>Loading…</div>
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>ScoreIvy Admin</h1>
        <p className={styles.subtitle}>
          {adminGateEnabled
            ? 'Sign in with a Google account listed in ADMIN_EMAILS.'
            : 'Sign in with any Google account (admin UI gate off for local dev).'}
        </p>

        <div className={styles.oauthHint}>
          <strong>Google OAuth:</strong> Add <code>http://localhost:3001</code> to{' '}
          <em>Authorized JavaScript origins</em> in Google Cloud Console. Missing this causes{' '}
          <em>origin_mismatch</em> (not an email case issue).
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={() =>
            setError(
              'Google login failed. If you see origin_mismatch, add http://localhost:3001 to Authorized JavaScript origins in Google Cloud Console.'
            )
          }
        />
      </div>
    </div>
  )
}

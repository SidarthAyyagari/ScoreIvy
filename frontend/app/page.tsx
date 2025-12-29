'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from './contexts/AuthContext'
import { apiJson } from './utils/api'
import styles from './page.module.css'

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  const [error, setError] = useState('')

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      setError('')
      
      // Decode the JWT token to get user info
      const base64Url = credentialResponse.credential.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      
      const userInfo = JSON.parse(jsonPayload)
      
      // Send to backend for OAuth login
      const response = await apiJson<{
        access_token: string
        user: {
          id: number
          email: string
          name: string | null
          picture: string | null
        }
      }>('/api/auth/oauth-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userInfo.email,
          name: userInfo.name,
          picture: userInfo.picture,
          oauth_provider: 'google',
          oauth_id: userInfo.sub,
        }),
      })
      
      // Store auth data
      login(response.user.email, response.user.name, response.user.picture, response.access_token)
      
      // Update user ID from response
      localStorage.setItem('user', JSON.stringify(response.user))
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.')
      console.error('Login error:', err)
    }
  }

  const handleGoogleError = () => {
    setError('Google login failed. Please try again.')
  }

  return (
    <div className={styles.container}>
      <div className={styles.loginCard}>
        <h1 className={styles.title}>ScoreIvy</h1>
        <p className={styles.subtitle}>Welcome! Sign in to continue.</p>
        
        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.oauthSection}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap
          />
        </div>
      </div>
    </div>
  )
}

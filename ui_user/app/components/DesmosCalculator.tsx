'use client'

import { useEffect, useRef, useState } from 'react'

declare global {
  interface Window {
    Desmos?: { GraphingCalculator: (el: HTMLElement, options?: object) => { destroy: () => void } }
  }
}

const DESMOS_API_KEY = process.env.NEXT_PUBLIC_DESMOS_API_KEY

function loadDesmos(): Promise<void> {
  if (window.Desmos) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const existing = document.getElementById('desmos-api') as HTMLScriptElement | null
    const script = existing ?? document.createElement('script')
    script.addEventListener('load', () => resolve())
    script.addEventListener('error', () => reject(new Error('Failed to load calculator')))
    if (!existing) {
      script.id = 'desmos-api'
      script.src = `https://www.desmos.com/api/v1.9/calculator.js?apiKey=${DESMOS_API_KEY}`
      document.body.appendChild(script)
    }
  })
}

export function DesmosCalculator() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(DESMOS_API_KEY ? null : 'Calculator is not configured.')

  useEffect(() => {
    if (!DESMOS_API_KEY || !containerRef.current) return
    let calculator: { destroy: () => void } | undefined
    let cancelled = false
    loadDesmos()
      .then(() => {
        if (!cancelled && containerRef.current && window.Desmos) {
          calculator = window.Desmos.GraphingCalculator(containerRef.current, { keypad: true })
        }
      })
      .catch((err: Error) => setError(err.message))
    return () => {
      cancelled = true
      calculator?.destroy()
    }
  }, [])

  if (error) return <p>{error}</p>
  return <div ref={containerRef} style={{ width: '100%', height: '480px' }} />
}

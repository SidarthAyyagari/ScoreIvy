import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ScoreIvy - Exam Platform',
  description: 'Take exams and track your scores',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}


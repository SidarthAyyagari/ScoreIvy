'use client'

import Link from 'next/link'
import { RESOURCES } from '../../lib/resources'
import styles from './page.module.css'

export default function DashboardPage() {
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Admin Dashboard</h1>
      <p className={styles.subtitle}>
        Manage all ScoreIvy data. Only users listed in ADMIN_EMAILS can access this app.
      </p>
      <div className={styles.grid}>
        {RESOURCES.map((resource) => (
          <Link key={resource.key} href={`/resources/${resource.key}`} className={styles.card}>
            <h2>{resource.label}</h2>
            <p>{resource.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}

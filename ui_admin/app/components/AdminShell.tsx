'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { RESOURCES } from '../lib/resources'
import styles from './AdminShell.module.css'

export function AdminShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const pathname = usePathname()

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <Link href="/dashboard">ScoreIvy Admin</Link>
        </div>
        <nav className={styles.nav}>
          <Link
            href="/dashboard"
            className={pathname === '/dashboard' ? styles.navActive : styles.navLink}
          >
            Dashboard
          </Link>
          {RESOURCES.map((resource) => (
            <Link
              key={resource.key}
              href={`/resources/${resource.key}`}
              className={
                pathname === `/resources/${resource.key}` ? styles.navActive : styles.navLink
              }
            >
              {resource.label}
            </Link>
          ))}
        </nav>
        <div className={styles.userBlock}>
          <span className={styles.userEmail}>{user?.email}</span>
          <button type="button" className={styles.logoutBtn} onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className={styles.main}>{children}</main>
    </div>
  )
}

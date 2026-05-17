'use client'

import { RequireAdmin } from '../components/RequireAdmin'
import { AdminShell } from '../components/AdminShell'

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAdmin>
      <AdminShell>{children}</AdminShell>
    </RequireAdmin>
  )
}

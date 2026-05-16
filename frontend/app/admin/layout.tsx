'use client'

import { RequireAdmin } from '../components/RequireAdmin'

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <RequireAdmin>{children}</RequireAdmin>
}

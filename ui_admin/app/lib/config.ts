/** When false, any authenticated Google user can use the admin UI (dev only). */
export function isAdminGateEnabled(): boolean {
  return process.env.NEXT_PUBLIC_REQUIRE_ADMIN !== 'false'
}

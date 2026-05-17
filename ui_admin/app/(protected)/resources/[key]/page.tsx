'use client'

import { notFound } from 'next/navigation'
import { CrudResource } from '../../../components/CrudResource'
import { getResource } from '../../../lib/resources'

export default function ResourcePage({ params }: { params: { key: string } }) {
  const resource = getResource(params.key)
  if (!resource) {
    notFound()
  }
  return <CrudResource resource={resource} />
}

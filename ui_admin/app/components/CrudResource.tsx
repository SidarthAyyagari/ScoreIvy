'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'
import { apiJson } from '../utils/api'
import { FieldDef, ResourceDef } from '../lib/resources'
import styles from './CrudResource.module.css'

type Row = Record<string, unknown>

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

function parseFieldValue(field: FieldDef, raw: string): unknown {
  if (raw === '' && !field.required) return null
  switch (field.type) {
    case 'number':
      return raw === '' ? null : Number(raw)
    case 'boolean':
      return raw === 'true'
    case 'json':
      return JSON.parse(raw)
    default:
      return raw
  }
}

function rowToForm(row: Row, fields: FieldDef[]): Record<string, string> {
  const form: Record<string, string> = {}
  for (const field of fields) {
    const val = row[field.name]
    if (val === null || val === undefined) {
      form[field.name] = ''
    } else if (field.type === 'json') {
      form[field.name] = JSON.stringify(val, null, 2)
    } else if (field.type === 'boolean') {
      form[field.name] = String(val)
    } else {
      form[field.name] = String(val)
    }
  }
  return form
}

export function CrudResource({ resource }: { resource: ResourceDef }) {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const apiBase = `/api/admin/${resource.apiPath}`
  const editableFields = resource.fields.filter((f) => !f.readOnly)
  const createFields = editableFields.filter((f) => !f.hideOnCreate)
  const displayColumns = resource.fields.filter((f) => f.name === 'id' || !f.hideOnCreate).slice(0, 6)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const data = await apiJson<Row[]>(apiBase)
      setRows(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [apiBase])

  useEffect(() => {
    load()
  }, [load])

  const openCreate = () => {
    const initial: Record<string, string> = {}
    for (const field of createFields) {
      if (field.type === 'boolean') initial[field.name] = 'true'
      else initial[field.name] = ''
    }
    setForm(initial)
    setEditingId(null)
    setModalOpen(true)
  }

  const openEdit = (row: Row) => {
    setForm(rowToForm(row, editableFields))
    setEditingId(row.id as number)
    setModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm(`Delete ${resource.label} #${id}?`)) return
    try {
      await apiJson(`${apiBase}/${id}`, { method: 'DELETE' })
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')

    const fields = editingId ? editableFields : createFields
    const payload: Record<string, unknown> = {}

    try {
      for (const field of fields) {
        if (field.readOnly || field.hideOnCreate && !editingId) continue
        const raw = form[field.name] ?? ''
        if (raw === '' && !field.required) continue
        payload[field.name] = parseFieldValue(field, raw)
      }

      if (editingId) {
        await apiJson(`${apiBase}/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
      } else {
        await apiJson(apiBase, {
          method: 'POST',
          body: JSON.stringify(payload),
        })
      }

      setModalOpen(false)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>{resource.label}</h1>
          <p className={styles.subtitle}>{resource.description}</p>
        </div>
        <button type="button" className={styles.primaryBtn} onClick={openCreate}>
          + New {resource.label.replace(/s$/, '')}
        </button>
      </header>

      {error && !modalOpen && <div className={styles.errorBanner}>{error}</div>}

      {loading ? (
        <p className={styles.muted}>Loading…</p>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                {displayColumns.map((col) => (
                  <th key={col.name}>{col.label}</th>
                ))}
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={displayColumns.length + 1} className={styles.empty}>
                    No records yet.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={String(row.id)}>
                    {displayColumns.map((col) => (
                      <td key={col.name} className={col.type === 'text' ? styles.cellWide : undefined}>
                        {formatCellValue(row[col.name])}
                      </td>
                    ))}
                    <td className={styles.actions}>
                      <button type="button" onClick={() => openEdit(row)}>
                        Edit
                      </button>
                      <button
                        type="button"
                        className={styles.dangerBtn}
                        onClick={() => handleDelete(row.id as number)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen && (
        <div className={styles.overlay} onClick={() => setModalOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2>{editingId ? `Edit #${editingId}` : `New ${resource.label.replace(/s$/, '')}`}</h2>
            {error && <div className={styles.errorBanner}>{error}</div>}
            <form onSubmit={handleSubmit} className={styles.form}>
              {(editingId ? editableFields : createFields).map((field) => (
                <label key={field.name} className={styles.field}>
                  <span>
                    {field.label}
                    {field.required ? ' *' : ''}
                  </span>
                  {field.type === 'boolean' ? (
                    <select
                      value={form[field.name] ?? 'true'}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, [field.name]: e.target.value }))
                      }
                    >
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  ) : field.type === 'text' || field.type === 'json' ? (
                    <textarea
                      rows={field.type === 'json' ? 5 : 3}
                      value={form[field.name] ?? ''}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, [field.name]: e.target.value }))
                      }
                      required={field.required}
                    />
                  ) : (
                    <input
                      type={
                        field.type === 'number'
                          ? 'number'
                          : field.type === 'email'
                            ? 'email'
                            : field.type === 'datetime'
                              ? 'datetime-local'
                              : 'text'
                      }
                      value={form[field.name] ?? ''}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, [field.name]: e.target.value }))
                      }
                      required={field.required}
                      readOnly={field.readOnly}
                    />
                  )}
                </label>
              ))}
              <div className={styles.formActions}>
                <button type="submit" className={styles.primaryBtn} disabled={submitting}>
                  {submitting ? 'Saving…' : 'Save'}
                </button>
                <button type="button" onClick={() => setModalOpen(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

import React, { useState, useEffect, FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Edit2, Trash2, Globe, X, Timer, RotateCw } from 'lucide-react'
import { targetsApi } from '../api'
import type { Target } from '../types'
import { AxiosError } from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useResizableTable } from '@/hooks/useResizableTable'

interface FormData {
  name: string
  url: string
  method: string
  headers: string
  body: string
  timeout_seconds: number | string
  retry_count: number | string
  retry_delay_seconds: number | string
  follow_redirects: boolean
}

function Targets() {
  const tableRef = useResizableTable()
  const [searchParams, setSearchParams] = useSearchParams()
  const [targets, setTargets] = useState<Target[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(searchParams.get('create') === 'true')
  const [editingTarget, setEditingTarget] = useState<Target | null>(null)
  const [formData, setFormData] = useState<FormData>({
    name: '',
    url: '',
    method: 'GET',
    headers: '{}',
    body: '',
    timeout_seconds: 30,
    retry_count: 0,
    retry_delay_seconds: 1,
    follow_redirects: true,
  })

  useEffect(() => {
    loadTargets()
  }, [])

  const loadTargets = async () => {
    try {
      setLoading(true)
      const response = await targetsApi.getAll()
      setTargets(response.data.data || [])
      setError(null)
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to load targets')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    try {
      let headers = {}
      try {
        headers = JSON.parse(formData.headers || '{}')
      } catch {
        throw new Error('Invalid JSON in headers')
      }

      let body = null
      if (formData.body) {
        try {
          body = JSON.parse(formData.body)
        } catch {
          throw new Error('Invalid JSON in body')
        }
      }

      const data = {
        name: formData.name,
        url: formData.url,
        method: formData.method,
        headers,
        body,
        timeout_seconds: parseInt(formData.timeout_seconds.toString()),
        retry_count: parseInt(formData.retry_count.toString()),
        retry_delay_seconds: parseInt(formData.retry_delay_seconds.toString()),
        follow_redirects: formData.follow_redirects,
      }

      if (editingTarget) {
        await targetsApi.update(editingTarget.id, data)
      } else {
        await targetsApi.create(data)
      }

      setShowForm(false)
      setEditingTarget(null)
      setFormData({
        name: '',
        url: '',
        method: 'GET',
        headers: '{}',
        body: '',
        timeout_seconds: 30,
        retry_count: 0,
        retry_delay_seconds: 1,
        follow_redirects: true,
      })
      loadTargets()
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }> | Error
      if ('response' in axiosError && axiosError.response) {
        setError(axiosError.response.data?.detail || 'Failed to save target')
      } else {
        setError((err as Error).message || 'Failed to save target')
      }
    }
  }

  const handleEdit = (target: Target) => {
    setEditingTarget(target)
    setFormData({
      name: target.name,
      url: target.url,
      method: target.method,
      headers: JSON.stringify(target.headers || {}, null, 2),
      body: target.body ? JSON.stringify(target.body, null, 2) : '',
      timeout_seconds: target.timeout_seconds || 30,
      retry_count: target.retry_count || 0,
      retry_delay_seconds: target.retry_delay_seconds || 1,
      follow_redirects: target.follow_redirects ?? true,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this target?')) return
    try {
      await targetsApi.delete(id)
      loadTargets()
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to delete target')
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingTarget(null)
    setSearchParams({})
    setFormData({
      name: '',
      url: '',
      method: 'GET',
      headers: '{}',
      body: '',
      timeout_seconds: 30,
      retry_count: 0,
      retry_delay_seconds: 1,
      follow_redirects: true,
    })
  }

  const toggleForm = () => {
    const newState = !showForm
    setShowForm(newState)
    if (newState) {
      setSearchParams({ create: 'true' })
    } else {
      setSearchParams({})
    }
  }

  if (loading && targets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full"
        />
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <Card className="border-slate-200/50 dark:border-slate-700/50 shadow-xl bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <Globe className="w-6 h-6 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl">Targets</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Configure HTTP endpoints to monitor
                </p>
              </div>
            </div>
            <Button 
              onClick={toggleForm}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              {showForm ? (
                <>
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Target
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="p-4 mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {showForm && (
              <motion.form
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                onSubmit={handleSubmit}
                className="mb-8 space-y-6 p-6 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700"
              >
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Target Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="My API Target"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="url">URL</Label>
                    <Input
                      id="url"
                      type="url"
                      value={formData.url}
                      onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                      placeholder="https://api.example.com"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="method">HTTP Method</Label>
                  <select
                    id="method"
                    value={formData.method}
                    onChange={(e) => setFormData({ ...formData, method: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="PATCH">PATCH</option>
                    <option value="DELETE">DELETE</option>
                  </select>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="timeout">Timeout (s)</Label>
                    <Input
                      id="timeout"
                      type="number"
                      value={formData.timeout_seconds}
                      onChange={(e) => setFormData({ ...formData, timeout_seconds: e.target.value })}
                      min="1"
                      max="300"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="retry">Retry Count</Label>
                    <Input
                      id="retry"
                      type="number"
                      value={formData.retry_count}
                      onChange={(e) => setFormData({ ...formData, retry_count: e.target.value })}
                      min="0"
                      max="10"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="delay">Retry Delay (s)</Label>
                    <Input
                      id="delay"
                      type="number"
                      value={formData.retry_delay_seconds}
                      onChange={(e) => setFormData({ ...formData, retry_delay_seconds: e.target.value })}
                      min="0"
                      max="60"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="headers">Headers (JSON)</Label>
                  <textarea
                    id="headers"
                    value={formData.headers}
                    onChange={(e) => setFormData({ ...formData, headers: e.target.value })}
                    className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring font-mono"
                    placeholder='{"Content-Type": "application/json"}'
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="body">Request Body (JSON, optional)</Label>
                  <textarea
                    id="body"
                    value={formData.body}
                    onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                    className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring font-mono"
                    placeholder='{"key": "value"}'
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="follow_redirects"
                    checked={formData.follow_redirects}
                    onChange={(e) => setFormData({ ...formData, follow_redirects: e.target.checked })}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <Label htmlFor="follow_redirects" className="cursor-pointer">
                    Follow HTTP redirects (301, 302, etc.)
                  </Label>
                </div>

                <div className="flex gap-3">
                  <Button type="submit" className="bg-gradient-to-r from-blue-600 to-purple-600">
                    {editingTarget ? 'Update Target' : 'Create Target'}
                  </Button>
                  <Button type="button" variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                </div>
              </motion.form>
            )}
          </AnimatePresence>

          <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-auto">
            <Table ref={tableRef} className="resizable-table">
              <TableHeader>
                <TableRow className="bg-slate-50 dark:bg-slate-900/50">
                  <TableHead>Name</TableHead>
                  <TableHead>URL</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>
                    <div className="flex items-center gap-2">
                      <Timer className="w-4 h-4" />
                      Timeout
                    </div>
                  </TableHead>
                  <TableHead>
                    <div className="flex items-center gap-2">
                      <RotateCw className="w-4 h-4" />
                      Retries
                    </div>
                  </TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <AnimatePresence>
                  {targets.map((target, index) => (
                    <motion.tr
                      key={target.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05 }}
                      className="group hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <TableCell className="font-medium">{target.name}</TableCell>
                      <TableCell className="font-mono text-xs truncate max-w-xs" title={target.url}>
                        {target.url}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">
                          {target.method}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{target.timeout_seconds}s</TableCell>
                      <TableCell className="font-mono text-sm">{target.retry_count}</TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(target)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(target.id)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </TableBody>
            </Table>
          </div>

          {targets.length === 0 && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <Globe className="w-16 h-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
              <p className="text-slate-600 dark:text-slate-400">
                No targets yet. Create your first target to get started.
              </p>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default Targets

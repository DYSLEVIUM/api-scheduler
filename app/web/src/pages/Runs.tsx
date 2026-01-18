import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import { AxiosError } from 'axios'
import { AnimatePresence, motion } from 'framer-motion'
import { Activity, ArrowRight, Calendar, Clock, Code, FileText, Filter, Link, Play, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { runsApi, schedulesApi } from '../api'
import type { Run, Schedule } from '../types'

interface Filters {
  schedule_id: string
  status: string
  start_time: string
  end_time: string
}

function Runs() {
  const tableRef = useResizableTable()
  const [searchParams, setSearchParams] = useSearchParams()
  const [runs, setRuns] = useState<Run[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<Filters>(() => ({
    schedule_id: searchParams.get('schedule_id') || '',
    status: searchParams.get('status') || '',
    start_time: searchParams.get('start_time') || '',
    end_time: searchParams.get('end_time') || '',
  }))
  const [selectedRun, setSelectedRun] = useState<Run | null>(null)

  useEffect(() => {
    loadSchedules()
  }, [])

  useEffect(() => {
    const scheduleIdParam = searchParams.get('schedule_id')
    const statusParam = searchParams.get('status')
    const startTimeParam = searchParams.get('start_time')
    const endTimeParam = searchParams.get('end_time')

    const newFilters = {
      schedule_id: scheduleIdParam || '',
      status: statusParam || '',
      start_time: startTimeParam || '',
      end_time: endTimeParam || '',
    }

    setFilters(prevFilters => {
      if (JSON.stringify(prevFilters) !== JSON.stringify(newFilters)) {
        return newFilters
      }
      return prevFilters
    })
  }, [searchParams])

  const loadSchedules = async () => {
    try {
      const response = await schedulesApi.getAll()
      setSchedules(response.data.data || [])
    } catch (err) {
      console.error('Failed to load schedules:', err)
    }
  }

  const loadRuns = async () => {
    try {
      setLoading(true)
      const params: Record<string, string> = {}
      if (filters.schedule_id) params.schedule_id = filters.schedule_id
      if (filters.status) params.status = filters.status
      if (filters.start_time) params.start_time = filters.start_time
      if (filters.end_time) params.end_time = filters.end_time

      const response = await runsApi.getAll(params)
      setRuns(response.data.data || [])
      setError(null)
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to load runs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRuns()
  }, [filters])

  const handleFilterChange = (key: keyof Filters, value: string) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    
    const params: Record<string, string> = {}
    Object.entries(newFilters).forEach(([k, v]) => {
      if (v) params[k] = v
    })
    setSearchParams(params)
  }

  const handleViewDetails = async (id: string) => {
    try {
      const response = await runsApi.getById(id)
      setSelectedRun(response.data.data)
      const params = Object.fromEntries(searchParams.entries())
      params.run_id = id
      setSearchParams(params)
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to load run details')
    }
  }

  const handleCloseDetails = () => {
    setSelectedRun(null)
    const params = Object.fromEntries(searchParams.entries())
    delete params.run_id
    setSearchParams(params)
  }

  useEffect(() => {
    const runId = searchParams.get('run_id')
    if (runId && !selectedRun) {
      handleViewDetails(runId)
    }
  }, [searchParams])

  const getStatusBadge = (status: string) => {
    const statusLower = status?.toLowerCase() || ''
    if (statusLower === 'success') return 'success'
    if (statusLower.includes('error') || statusLower.includes('timeout')) return 'error'
    if (statusLower.includes('4xx') || statusLower.includes('5xx')) return 'warning'
    return 'default'
  }

  const getScheduleName = (run: Run) => {
    if (run.name) {
      return run.name
    }
    const schedule = schedules.find(s => s.id === run.schedule_id)
    return schedule?.name || `Schedule ${run.schedule_id.slice(0, 8)}...`
  }

  if (loading && runs.length === 0) {
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
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <Play className="w-6 h-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-2xl">Runs</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                View execution history and results
              </p>
            </div>
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

          <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-4 h-4 text-slate-600 dark:text-slate-400" />
              <span className="font-medium text-sm">Filters</span>
              {filters.schedule_id && (
                <Badge variant="default" className="ml-2">
                  Schedule Filtered
                </Badge>
              )}
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label htmlFor="schedule">Schedule</Label>
                <select
                  id="schedule"
                  value={filters.schedule_id}
                  onChange={(e) => handleFilterChange('schedule_id', e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">All Schedules</option>
                  {schedules.map((schedule) => (
                    <option key={schedule.id} value={schedule.id}>
                      {schedule.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">All Statuses</option>
                  <option value="success">Success</option>
                  <option value="timeout">Timeout</option>
                  <option value="dns_error">DNS Error</option>
                  <option value="connection_error">Connection Error</option>
                  <option value="http_4xx">HTTP 4xx</option>
                  <option value="http_5xx">HTTP 5xx</option>
                  <option value="error">Error</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="startTime">Start Time</Label>
                <Input
                  id="startTime"
                  type="datetime-local"
                  value={filters.start_time}
                  onChange={(e) => handleFilterChange('start_time', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="endTime">End Time</Label>
                <Input
                  id="endTime"
                  type="datetime-local"
                  value={filters.end_time}
                  onChange={(e) => handleFilterChange('end_time', e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-auto">
            <Table ref={tableRef} className="resizable-table">
              <TableHeader>
                <TableRow className="bg-slate-50 dark:bg-slate-900/50">
                  <TableHead className="cursor-col-resize">Run #</TableHead>
                  <TableHead className="cursor-col-resize">Schedule Name</TableHead>
                  <TableHead className="cursor-col-resize">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Started At
                    </div>
                  </TableHead>
                  <TableHead className="cursor-col-resize">Status</TableHead>
                  <TableHead className="cursor-col-resize">
                    <div className="flex items-center gap-2">
                      <Code className="w-4 h-4" />
                      Code
                    </div>
                  </TableHead>
                  <TableHead className="cursor-col-resize">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Latency
                    </div>
                  </TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <AnimatePresence>
                  {runs.map((run, index) => (
                    <motion.tr
                      key={run.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05 }}
                      className="group hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <TableCell className="font-mono font-medium">{run.run_number}</TableCell>
                      <TableCell className="text-sm" title={run.schedule_id}>
                        {getScheduleName(run)}
                      </TableCell>
                      <TableCell className="text-sm">
                        {new Date(run.started_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadge(run.status) as any}>
                          {run.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {run.status_code || 'N/A'}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {run.latency_ms ? `${run.latency_ms.toFixed(2)}ms` : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleViewDetails(run.id)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Activity className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </TableBody>
            </Table>
          </div>

          {runs.length === 0 && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <Play className="w-16 h-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
              <p className="text-slate-600 dark:text-slate-400">
                No runs found. Create a schedule to start executing requests.
              </p>
            </motion.div>
          )}
        </CardContent>
      </Card>

      <AnimatePresence>
        {selectedRun && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card className="border-slate-200/50 dark:border-slate-700/50 shadow-xl bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl">
                      <Activity className="w-6 h-6 text-white" />
                    </div>
                    <CardTitle className="text-2xl">Run Details</CardTitle>
                  </div>
                  <Button variant="ghost" onClick={handleCloseDetails}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Run Number</p>
                    <p className="font-mono font-semibold text-lg">{selectedRun.run_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Schedule ID</p>
                    <p className="font-mono text-sm">{selectedRun.schedule_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Started At</p>
                    <p className="text-sm">{new Date(selectedRun.started_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Status</p>
                    <Badge variant={getStatusBadge(selectedRun.status) as any} className="text-sm">
                      {selectedRun.status}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Status Code</p>
                    <p className="font-mono font-semibold">{selectedRun.status_code || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Latency</p>
                    <p className="font-mono font-semibold">
                      {selectedRun.latency_ms ? `${selectedRun.latency_ms.toFixed(2)}ms` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Response Size</p>
                    <p className="font-mono">
                      {selectedRun.response_size_bytes ? `${selectedRun.response_size_bytes} bytes` : 'N/A'}
                    </p>
                  </div>
                  {selectedRun.redirected && (
                    <div className="col-span-2">
                      <div className="flex items-center gap-2 mb-2">
                        <Link className="w-4 h-4 text-blue-600" />
                        <p className="font-medium">Redirects</p>
                        <Badge variant="outline" className="ml-2">
                          {selectedRun.redirect_count} redirect{selectedRun.redirect_count !== 1 ? 's' : ''}
                        </Badge>
                      </div>
                      {selectedRun.redirect_history && selectedRun.redirect_history.length > 0 && (
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                          <div className="space-y-2">
                            {selectedRun.redirect_history.map((redirect, index) => (
                              <div key={index} className="flex items-center gap-2 text-sm">
                                <ArrowRight className="w-4 h-4 text-blue-600" />
                                <span className="font-mono text-xs">{redirect.status_code}</span>
                                <span className="text-xs text-muted-foreground truncate">{redirect.url}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {selectedRun.error_message && (
                    <div className="col-span-2">
                      <p className="text-sm text-muted-foreground mb-1">Error Message</p>
                      <p className="text-sm text-red-600 dark:text-red-400 font-mono p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                        {selectedRun.error_message}
                      </p>
                    </div>
                  )}
                </div>

                {selectedRun.response_headers && Object.keys(selectedRun.response_headers).length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4" />
                      <p className="font-medium">Response Headers</p>
                    </div>
                    <pre className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700 overflow-auto text-xs font-mono">
                      {JSON.stringify(selectedRun.response_headers, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedRun.response_body && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Code className="w-4 h-4" />
                      <p className="font-medium">Response Body</p>
                    </div>
                    <pre className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700 overflow-auto max-h-96 text-xs font-mono">
                      {typeof selectedRun.response_body === 'string'
                        ? selectedRun.response_body
                        : JSON.stringify(selectedRun.response_body, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default Runs

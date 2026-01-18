import React, { useState, useEffect, FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Play, Pause, Trash2, Eye, Clock, Timer, X, Calendar, Globe, Activity } from 'lucide-react'
import { schedulesApi, targetsApi } from '../api'
import type { Schedule, Target } from '../types'
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
  target_id: string
  schedule_type: 'interval' | 'window'
  interval_seconds: number | string
  duration_seconds: number | string
}

function Schedules() {
  const tableRef = useResizableTable()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [targets, setTargets] = useState<Target[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(searchParams.get('create') === 'true')
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null)
  const [formData, setFormData] = useState<FormData>({
    name: '',
    target_id: '',
    schedule_type: 'interval',
    interval_seconds: 60,
    duration_seconds: 3600,
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [schedulesRes, targetsRes] = await Promise.all([
        schedulesApi.getAll(),
        targetsApi.getAll(),
      ])
      setSchedules(schedulesRes.data.data || [])
      setTargets(targetsRes.data.data || [])
      setError(null)
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handlePause = async (id: string) => {
    try {
      await schedulesApi.pause(id)
      loadData()
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to pause schedule')
    }
  }

  const handleResume = async (id: string) => {
    try {
      await schedulesApi.resume(id)
      loadData()
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to resume schedule')
    }
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    try {
      const data: Record<string, unknown> = {
        name: formData.name,
        target_id: formData.target_id,
        interval_seconds: parseInt(formData.interval_seconds.toString()),
      }

      if (formData.schedule_type === 'window') {
        data.duration_seconds = parseInt(formData.duration_seconds.toString())
      }

      await schedulesApi.create(data)

      setShowForm(false)
      setFormData({
        name: '',
        target_id: '',
        schedule_type: 'interval',
        interval_seconds: 60,
        duration_seconds: 3600,
      })
      loadData()
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to save schedule')
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this schedule? All runs will also be deleted.')) return
    try {
      await schedulesApi.delete(id)
      loadData()
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(axiosError.response?.data?.detail || 'Failed to delete schedule')
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setSearchParams({})
    setFormData({
      name: '',
      target_id: '',
      schedule_type: 'interval',
      interval_seconds: 60,
      duration_seconds: 3600,
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

  const getTargetName = (targetId: string) => {
    const target = targets.find(t => t.id === targetId)
    return target ? target.name : targetId.slice(0, 8) + '...'
  }

  const getTarget = (targetId: string) => {
    return targets.find(t => t.id === targetId)
  }

  const handleScheduleClick = (schedule: Schedule) => {
    setSelectedSchedule(schedule)
    const params = Object.fromEntries(searchParams.entries())
    params.schedule_id = schedule.id
    setSearchParams(params)
  }

  const handleCloseDetails = () => {
    setSelectedSchedule(null)
    const params = Object.fromEntries(searchParams.entries())
    delete params.schedule_id
    setSearchParams(params)
  }

  const handleViewRuns = (scheduleId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    navigate(`/runs?schedule_id=${scheduleId}`)
  }

  useEffect(() => {
    const scheduleId = searchParams.get('schedule_id')
    if (scheduleId && schedules.length > 0 && !selectedSchedule) {
      const schedule = schedules.find(s => s.id === scheduleId)
      if (schedule) {
        setSelectedSchedule(schedule)
      }
    }
  }, [searchParams, schedules])

  if (loading && schedules.length === 0) {
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
                <Clock className="w-6 h-6 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl">Schedules</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Manage your API request schedules
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
                  Create Schedule
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
                <div className="space-y-2">
                  <Label htmlFor="name">Schedule Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Daily Health Check"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target">Target</Label>
                  <select
                    id="target"
                    value={formData.target_id}
                    onChange={(e) => setFormData({ ...formData, target_id: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    required
                  >
                    <option value="">Select a target</option>
                    {targets.map((target) => (
                      <option key={target.id} value={target.id}>
                        {target.name} - {target.url}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="scheduleType">Schedule Type</Label>
                  <select
                    id="scheduleType"
                    value={formData.schedule_type}
                    onChange={(e) => setFormData({ ...formData, schedule_type: e.target.value as 'interval' | 'window' })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <option value="interval">Interval (runs every N seconds)</option>
                    <option value="window">Window (runs for M seconds)</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="interval">Interval (seconds)</Label>
                    <Input
                      id="interval"
                      type="number"
                      value={formData.interval_seconds}
                      onChange={(e) => setFormData({ ...formData, interval_seconds: e.target.value })}
                      min="1"
                      required
                    />
                  </div>
                  {formData.schedule_type === 'window' && (
                    <div className="space-y-2">
                      <Label htmlFor="duration">Duration (seconds)</Label>
                      <Input
                        id="duration"
                        type="number"
                        value={formData.duration_seconds}
                        onChange={(e) => setFormData({ ...formData, duration_seconds: e.target.value })}
                        min="1"
                        required
                      />
                    </div>
                  )}
                </div>

                <div className="flex gap-3">
                  <Button type="submit" className="bg-gradient-to-r from-blue-600 to-purple-600">
                    Create Schedule
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
                  <TableHead className="cursor-col-resize">Name</TableHead>
                  <TableHead className="cursor-col-resize">Target</TableHead>
                  <TableHead className="cursor-col-resize">Type</TableHead>
                  <TableHead className="cursor-col-resize">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Interval
                    </div>
                  </TableHead>
                  <TableHead className="cursor-col-resize">
                    <div className="flex items-center gap-2">
                      <Timer className="w-4 h-4" />
                      Duration
                    </div>
                  </TableHead>
                  <TableHead className="cursor-col-resize">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <AnimatePresence>
                  {schedules.map((schedule, index) => (
                    <motion.tr
                      key={schedule.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05 }}
                      onClick={() => handleScheduleClick(schedule)}
                      className="group hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer"
                    >
                      <TableCell className="font-medium">
                        {schedule.name}
                      </TableCell>
                      <TableCell className="text-sm">
                        {getTargetName(schedule.target_id)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">
                          {schedule.duration_seconds ? 'Window' : 'Interval'}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {schedule.interval_seconds}s
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {schedule.duration_seconds ? `${schedule.duration_seconds}s` : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={schedule.paused ? 'warning' : 'success'}>
                          {schedule.paused ? 'Paused' : 'Active'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => handleViewRuns(schedule.id, e)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {schedule.paused ? (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleResume(schedule.id)
                              }}
                              className="opacity-0 group-hover:opacity-100 transition-opacity text-green-600 hover:text-green-700"
                            >
                              <Play className="w-4 h-4" />
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation()
                                handlePause(schedule.id)
                              }}
                              className="opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <Pause className="w-4 h-4" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDelete(schedule.id)
                            }}
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

          {schedules.length === 0 && !loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <Clock className="w-16 h-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
              <p className="text-slate-600 dark:text-slate-400">
                No schedules yet. Create your first schedule to get started.
              </p>
            </motion.div>
          )}
        </CardContent>
      </Card>

      <AnimatePresence>
        {selectedSchedule && (
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
                    <CardTitle className="text-2xl">Schedule Details</CardTitle>
                  </div>
                  <Button variant="ghost" onClick={handleCloseDetails}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Schedule Name</p>
                    <p className="font-semibold text-lg">{selectedSchedule.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Status</p>
                    <Badge variant={selectedSchedule.paused ? 'warning' : 'success'}>
                      {selectedSchedule.paused ? 'Paused' : 'Active'}
                    </Badge>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-muted-foreground mb-1">Schedule ID</p>
                    <p className="font-mono text-sm">{selectedSchedule.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Target</p>
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-muted-foreground" />
                      <p className="font-medium">{getTargetName(selectedSchedule.target_id)}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Type</p>
                    <Badge variant="outline" className="font-mono">
                      {selectedSchedule.duration_seconds ? 'Window' : 'Interval'}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Interval
                      </div>
                    </p>
                    <p className="font-mono font-semibold text-lg">{selectedSchedule.interval_seconds}s</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">
                      <div className="flex items-center gap-2">
                        <Timer className="w-4 h-4" />
                        Duration
                      </div>
                    </p>
                    <p className="font-mono font-semibold text-lg">
                      {selectedSchedule.duration_seconds ? `${selectedSchedule.duration_seconds}s` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Created At
                      </div>
                    </p>
                    <p className="text-sm">{new Date(selectedSchedule.created_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Updated At
                      </div>
                    </p>
                    <p className="text-sm">{new Date(selectedSchedule.updated_at).toLocaleString()}</p>
                  </div>
                  {selectedSchedule.temporal_workflow_id && (
                    <div className="col-span-2">
                      <p className="text-sm text-muted-foreground mb-1">Temporal Workflow ID</p>
                      <p className="font-mono text-xs p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
                        {selectedSchedule.temporal_workflow_id}
                      </p>
                    </div>
                  )}
                </div>

                {getTarget(selectedSchedule.target_id) && (
                  <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                    <p className="text-sm text-muted-foreground mb-2">Target</p>
                    <Button
                      variant="outline"
                      onClick={() => navigate('/targets')}
                      className="flex items-center gap-2 w-full justify-start"
                    >
                      <Globe className="w-4 h-4" />
                      <div className="flex flex-col items-start">
                        <span className="font-medium">{getTarget(selectedSchedule.target_id)?.name}</span>
                        <span className="text-xs text-muted-foreground font-mono">{selectedSchedule.target_id}</span>
                      </div>
                    </Button>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <Button 
                    onClick={(e) => {
                      e.stopPropagation()
                      handleViewRuns(selectedSchedule.id, e)
                    }}
                    className="bg-gradient-to-r from-blue-600 to-purple-600"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Runs
                  </Button>
                  {selectedSchedule.paused ? (
                    <Button 
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleResume(selectedSchedule.id)
                        handleCloseDetails()
                      }}
                      className="text-green-600 hover:text-green-700"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Resume Schedule
                    </Button>
                  ) : (
                    <Button 
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation()
                        handlePause(selectedSchedule.id)
                        handleCloseDetails()
                      }}
                    >
                      <Pause className="w-4 h-4 mr-2" />
                      Pause Schedule
                    </Button>
                  )}
                  <Button 
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(selectedSchedule.id)
                      handleCloseDetails()
                    }}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Schedule
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default Schedules

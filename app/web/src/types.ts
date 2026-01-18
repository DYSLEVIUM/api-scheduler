export interface Target {
  id: string
  name: string
  url: string
  method: string
  headers?: Record<string, string>
  body?: Record<string, unknown>
  timeout_seconds: number
  retry_count: number
  retry_delay_seconds: number
  follow_redirects: boolean
  created_at: string
  updated_at: string
}

export interface Schedule {
  id: string
  name: string
  target_id: string
  interval_seconds: number
  duration_seconds?: number
  paused: boolean
  temporal_workflow_id?: string
  created_at: string
  updated_at: string
}

export interface Run {
  id: string
  schedule_id: string
  name?: string
  run_number: number
  started_at: string
  status: 'success' | 'failed' | 'pending'
  status_code?: number
  latency_ms?: number
  response_size_bytes?: number
  response_headers?: Record<string, string>
  response_body?: Record<string, unknown> | string
  error_message?: string
  redirected?: boolean
  redirect_count?: number
  redirect_history?: Array<{ url: string; status_code: number }>
  created_at: string
  updated_at: string
}

export interface APIResponse<T> {
  success: boolean
  status_code: number
  message: string
  data: T
}

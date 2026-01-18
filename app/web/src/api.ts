import axios, { AxiosInstance } from 'axios'
import type { Target, Schedule, Run, APIResponse } from './types'

const getApiUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL as string
  }
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }
  return `${window.location.protocol}//${window.location.hostname}:8000`
}

const API_BASE_URL = getApiUrl()

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const targetsApi = {
  getAll: () => api.get<APIResponse<Target[]>>('/targets'),
  getById: (id: string) => api.get<APIResponse<Target>>(`/targets/${id}`),
  create: (data: Partial<Target>) => api.post<APIResponse<Target>>('/targets', data),
  update: (id: string, data: Partial<Target>) => api.put<APIResponse<Target>>(`/targets/${id}`, data),
  delete: (id: string) => api.delete<APIResponse<Target>>(`/targets/${id}`),
}

export const schedulesApi = {
  getAll: () => api.get<APIResponse<Schedule[]>>('/schedules'),
  getById: (id: string) => api.get<APIResponse<Schedule>>(`/schedules/${id}`),
  create: (data: Partial<Schedule>) => api.post<APIResponse<Schedule>>('/schedules', data),
  update: (id: string, data: Partial<Schedule>) => api.put<APIResponse<Schedule>>(`/schedules/${id}`, data),
  delete: (id: string) => api.delete<APIResponse<Schedule>>(`/schedules/${id}`),
  pause: (id: string) => api.post<APIResponse<Schedule>>(`/schedules/${id}/pause`),
  resume: (id: string) => api.post<APIResponse<Schedule>>(`/schedules/${id}/resume`),
  getRuns: (id: string, params?: Record<string, string>) => api.get<APIResponse<Run[]>>(`/schedules/${id}/runs`, { params }),
}

export const runsApi = {
  getAll: (params?: Record<string, string>) => api.get<APIResponse<Run[]>>('/runs', { params }),
  getById: (id: string) => api.get<APIResponse<Run>>(`/runs/${id}`),
}

export default api

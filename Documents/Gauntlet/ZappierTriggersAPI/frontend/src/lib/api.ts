const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

interface RequestOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const apiKey = localStorage.getItem('api_key') || ''

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      ...options.headers,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail?.detail || error.detail || 'Request failed')
  }

  return response.json()
}

// Types
export interface Event {
  id: string
  event_type: string
  source: string
  data: Record<string, unknown>
  metadata?: Record<string, unknown>
  status: 'pending' | 'processing' | 'delivered' | 'partially_delivered' | 'failed'
  created_at: string
  updated_at?: string
  delivery_attempts: number
  successful_deliveries: number
  failed_deliveries: number
}

export interface InboxItem {
  event_id: string
  event_type: string
  source: string
  data: Record<string, unknown>
  receipt_handle: string
  received_at: string
}

export interface DLQItem {
  event_id: string
  event_type: string
  source: string
  data: Record<string, unknown>
  failure_reason?: string
  retry_count: number
  created_at: string
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    limit: number
    has_more: boolean
    next_cursor?: string
    total?: number
  }
}

export interface HealthStatus {
  status: string
  version?: string
  components?: Record<string, string>
}

// API functions
export const api = {
  // Health
  health: () => request<HealthStatus>('/health'),

  // Events
  events: {
    list: (params?: { limit?: number; cursor?: string; event_type?: string; status?: string }) => {
      const searchParams = new URLSearchParams()
      if (params?.limit) searchParams.set('limit', params.limit.toString())
      if (params?.cursor) searchParams.set('cursor', params.cursor)
      if (params?.event_type) searchParams.set('event_type', params.event_type)
      if (params?.status) searchParams.set('status', params.status)
      return request<PaginatedResponse<Event>>(`/events?${searchParams}`)
    },
    get: (id: string) => request<Event>(`/events/${id}`),
    create: (data: { event_type: string; source: string; data: unknown }) =>
      request<Event>('/events', { method: 'POST', body: data }),
    replay: (id: string, dryRun = false) =>
      request(`/events/${id}/replay`, { method: 'POST', body: { dry_run: dryRun } }),
  },

  // Inbox
  inbox: {
    list: (params?: { limit?: number }) => {
      const searchParams = new URLSearchParams()
      if (params?.limit) searchParams.set('limit', params.limit.toString())
      return request<PaginatedResponse<InboxItem>>(`/inbox?${searchParams}`)
    },
    acknowledge: (receiptHandles: string[]) =>
      request('/inbox/ack', { method: 'POST', body: { receipt_handles: receiptHandles } }),
  },

  // DLQ
  dlq: {
    list: (params?: { limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams()
      if (params?.limit) searchParams.set('limit', params.limit.toString())
      if (params?.offset) searchParams.set('offset', params.offset.toString())
      return request<PaginatedResponse<DLQItem>>(`/dlq?${searchParams}`)
    },
    retry: (eventId: string) =>
      request(`/dlq/${eventId}/retry`, { method: 'POST' }),
    dismiss: (eventId: string) =>
      request(`/dlq/${eventId}`, { method: 'DELETE' }),
  },
}

import { useEffect, useState } from 'react'
import { api, Event } from '../lib/api'
import {
  Zap,
  RefreshCw,
  Plus,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  Clock,
  Activity,
  X,
  Play,
} from 'lucide-react'

export default function Events() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [cursor, setCursor] = useState<string | undefined>()
  const [hasMore, setHasMore] = useState(false)
  const [filter, setFilter] = useState({ event_type: '', status: '' })
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)

  const fetchEvents = async (reset = false) => {
    setLoading(true)
    try {
      const response = await api.events.list({
        limit: 20,
        cursor: reset ? undefined : cursor,
        event_type: filter.event_type || undefined,
        status: filter.status || undefined,
      })
      setEvents(reset ? response.data : [...events, ...response.data])
      setCursor(response.pagination.next_cursor)
      setHasMore(response.pagination.has_more)
    } catch (err) {
      console.error('Failed to fetch events:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvents(true)
  }, [filter])

  const handleReplay = async (event: Event) => {
    try {
      await api.events.replay(event.id)
      fetchEvents(true)
    } catch (err) {
      console.error('Failed to replay event:', err)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'text-volt bg-volt/10 border-volt/30'
      case 'failed':
        return 'text-pulse bg-pulse/10 border-pulse/30'
      case 'processing':
        return 'text-arc bg-arc/10 border-arc/30'
      case 'partially_delivered':
        return 'text-spark bg-spark/10 border-spark/30'
      default:
        return 'text-mist bg-smoke/30 border-smoke/30'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
        return <CheckCircle className="w-3 h-3" />
      case 'failed':
        return <AlertTriangle className="w-3 h-3" />
      case 'processing':
        return <Activity className="w-3 h-3" />
      default:
        return <Clock className="w-3 h-3" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-cloud">Events</h1>
          <p className="text-ash text-sm mt-1">View and manage event history</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchEvents(true)}
            className="p-2 rounded-lg bg-slate/50 border border-smoke/30 hover:border-smoke/50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 text-mist ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-volt/10 border border-volt/30 text-volt hover:bg-volt/20 transition-colors glow-volt"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">Create Event</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Filter by event type..."
            value={filter.event_type}
            onChange={(e) => setFilter({ ...filter, event_type: e.target.value })}
            className="w-full px-4 py-2 bg-slate/50 border border-smoke/30 rounded-lg text-cloud text-sm placeholder-ash focus:outline-none focus:border-volt/50"
          />
        </div>
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="px-4 py-2 bg-slate/50 border border-smoke/30 rounded-lg text-cloud text-sm focus:outline-none focus:border-volt/50"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="delivered">Delivered</option>
          <option value="partially_delivered">Partial</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Events List */}
      <div className="bg-abyss/50 rounded-xl border border-smoke/30 overflow-hidden">
        {loading && events.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <Activity className="w-6 h-6 text-volt animate-pulse" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-16">
            <Zap className="w-10 h-10 text-smoke mx-auto mb-3" />
            <p className="text-ash">No events found</p>
          </div>
        ) : (
          <div className="divide-y divide-smoke/20">
            {events.map((event) => (
              <div
                key={event.id}
                onClick={() => setSelectedEvent(event)}
                className="p-4 hover:bg-slate/20 cursor-pointer transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${getStatusColor(event.status)}`}>
                      {getStatusIcon(event.status)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-cloud">{event.event_type}</span>
                        <span className="text-xs font-mono text-ash bg-smoke/50 px-2 py-0.5 rounded">
                          {event.source}
                        </span>
                      </div>
                      <span className="text-xs font-mono text-ash">{event.id}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="flex items-center gap-2 text-xs text-ash">
                        <span>{event.delivery_attempts} attempts</span>
                        <span className="text-volt">{event.successful_deliveries} ok</span>
                        {event.failed_deliveries > 0 && (
                          <span className="text-pulse">{event.failed_deliveries} failed</span>
                        )}
                      </div>
                      <p className="text-xs text-ash mt-1">
                        {new Date(event.created_at).toLocaleString()}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-ash" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Load More */}
        {hasMore && (
          <div className="p-4 border-t border-smoke/20">
            <button
              onClick={() => fetchEvents()}
              disabled={loading}
              className="w-full py-2 text-sm text-arc hover:text-volt transition-colors"
            >
              {loading ? 'Loading...' : 'Load more events'}
            </button>
          </div>
        )}
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onReplay={handleReplay}
        />
      )}

      {/* Create Event Modal */}
      {showCreateModal && (
        <CreateEventModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false)
            fetchEvents(true)
          }}
        />
      )}
    </div>
  )
}

interface EventDetailModalProps {
  event: Event
  onClose: () => void
  onReplay: (event: Event) => void
}

function EventDetailModal({ event, onClose, onReplay }: EventDetailModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-sm">
      <div className="bg-abyss border border-smoke/30 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-smoke/30">
          <h2 className="text-lg font-display font-semibold text-cloud">Event Details</h2>
          <button onClick={onClose} className="p-1 hover:bg-smoke/30 rounded transition-colors">
            <X className="w-5 h-5 text-ash" />
          </button>
        </div>

        <div className="p-4 space-y-4 overflow-y-auto max-h-[60vh]">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono text-ash uppercase">Event ID</label>
              <p className="text-sm font-mono text-cloud mt-1">{event.id}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Status</label>
              <p className="text-sm font-mono text-volt mt-1 uppercase">{event.status}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Event Type</label>
              <p className="text-sm text-cloud mt-1">{event.event_type}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Source</label>
              <p className="text-sm text-cloud mt-1">{event.source}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Created</label>
              <p className="text-sm text-cloud mt-1">{new Date(event.created_at).toLocaleString()}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Deliveries</label>
              <p className="text-sm text-cloud mt-1">
                {event.successful_deliveries}/{event.delivery_attempts} successful
              </p>
            </div>
          </div>

          <div>
            <label className="text-xs font-mono text-ash uppercase">Payload</label>
            <pre className="mt-2 p-4 bg-slate/50 rounded-lg text-xs font-mono text-cloud overflow-x-auto">
              {JSON.stringify(event.data, null, 2)}
            </pre>
          </div>

          {event.metadata && Object.keys(event.metadata).length > 0 && (
            <div>
              <label className="text-xs font-mono text-ash uppercase">Metadata</label>
              <pre className="mt-2 p-4 bg-slate/50 rounded-lg text-xs font-mono text-cloud overflow-x-auto">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-smoke/30 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-mist hover:text-cloud transition-colors"
          >
            Close
          </button>
          <button
            onClick={() => {
              onReplay(event)
              onClose()
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-arc/10 border border-arc/30 text-arc hover:bg-arc/20 transition-colors"
          >
            <Play className="w-4 h-4" />
            <span className="text-sm font-medium">Replay Event</span>
          </button>
        </div>
      </div>
    </div>
  )
}

interface CreateEventModalProps {
  onClose: () => void
  onCreated: () => void
}

function CreateEventModal({ onClose, onCreated }: CreateEventModalProps) {
  const [eventType, setEventType] = useState('')
  const [source, setSource] = useState('')
  const [data, setData] = useState('{}')
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    setError('')

    if (!eventType.trim()) {
      setError('Event type is required')
      return
    }

    if (!source.trim()) {
      setError('Source is required')
      return
    }

    let parsedData
    try {
      parsedData = JSON.parse(data)
    } catch {
      setError('Invalid JSON payload')
      return
    }

    setCreating(true)
    try {
      await api.events.create({
        event_type: eventType,
        source,
        data: parsedData,
      })
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create event')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-sm">
      <div className="bg-abyss border border-smoke/30 rounded-xl w-full max-w-lg">
        <div className="flex items-center justify-between p-4 border-b border-smoke/30">
          <h2 className="text-lg font-display font-semibold text-cloud">Create Event</h2>
          <button onClick={onClose} className="p-1 hover:bg-smoke/30 rounded transition-colors">
            <X className="w-5 h-5 text-ash" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {error && (
            <div className="p-3 bg-pulse/10 border border-pulse/30 rounded-lg text-pulse text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-mono text-ash uppercase mb-2">Event Type</label>
            <input
              type="text"
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              placeholder="user.created"
              className="w-full px-4 py-2 bg-slate/50 border border-smoke/30 rounded-lg text-cloud text-sm placeholder-ash focus:outline-none focus:border-volt/50"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-ash uppercase mb-2">Source</label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="my-app"
              className="w-full px-4 py-2 bg-slate/50 border border-smoke/30 rounded-lg text-cloud text-sm placeholder-ash focus:outline-none focus:border-volt/50"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-ash uppercase mb-2">Payload (JSON)</label>
            <textarea
              value={data}
              onChange={(e) => setData(e.target.value)}
              rows={6}
              className="w-full px-4 py-2 bg-slate/50 border border-smoke/30 rounded-lg text-cloud text-sm font-mono placeholder-ash focus:outline-none focus:border-volt/50 resize-none"
            />
          </div>
        </div>

        <div className="p-4 border-t border-smoke/30 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-mist hover:text-cloud transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-volt/10 border border-volt/30 text-volt hover:bg-volt/20 transition-colors disabled:opacity-50"
          >
            <Zap className="w-4 h-4" />
            <span className="text-sm font-medium">{creating ? 'Creating...' : 'Create Event'}</span>
          </button>
        </div>
      </div>
    </div>
  )
}

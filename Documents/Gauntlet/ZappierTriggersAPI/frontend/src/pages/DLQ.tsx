import { useEffect, useState } from 'react'
import { api, DLQItem } from '../lib/api'
import {
  AlertTriangle,
  RefreshCw,
  RotateCcw,
  Trash2,
  Activity,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

export default function DLQ() {
  const [items, setItems] = useState<DLQItem[]>([])
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [selectedItem, setSelectedItem] = useState<DLQItem | null>(null)
  const limit = 20

  const fetchDLQ = async (newOffset = 0) => {
    setLoading(true)
    try {
      const response = await api.dlq.list({ limit, offset: newOffset })
      setItems(response.data)
      setOffset(newOffset)
      setHasMore(response.pagination.has_more)
    } catch (err) {
      console.error('Failed to fetch DLQ:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDLQ()
  }, [])

  const handleRetry = async (item: DLQItem) => {
    try {
      await api.dlq.retry(item.event_id)
      fetchDLQ(offset)
    } catch (err) {
      console.error('Failed to retry:', err)
    }
  }

  const handleDismiss = async (item: DLQItem) => {
    try {
      await api.dlq.dismiss(item.event_id)
      fetchDLQ(offset)
    } catch (err) {
      console.error('Failed to dismiss:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-cloud flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-pulse" />
            Dead Letter Queue
          </h1>
          <p className="text-ash text-sm mt-1">Failed events awaiting manual intervention</p>
        </div>
        <button
          onClick={() => fetchDLQ(0)}
          className="p-2 rounded-lg bg-slate/50 border border-smoke/30 hover:border-smoke/50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-mist ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-2 p-3 bg-pulse/10 border border-pulse/30 rounded-lg">
        <AlertTriangle className="w-4 h-4 text-pulse" />
        <span className="text-sm text-pulse">
          {items.length > 0
            ? `${items.length} failed event${items.length !== 1 ? 's' : ''} require attention`
            : 'No failed events'}
        </span>
      </div>

      {/* DLQ List */}
      <div className="bg-abyss/50 rounded-xl border border-smoke/30 overflow-hidden">
        {loading && items.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <Activity className="w-6 h-6 text-volt animate-pulse" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-16">
            <AlertTriangle className="w-10 h-10 text-smoke mx-auto mb-3" />
            <p className="text-ash">DLQ is empty</p>
            <p className="text-xs text-ash/60 mt-1">All events processed successfully</p>
          </div>
        ) : (
          <div className="divide-y divide-smoke/20">
            {items.map((item) => (
              <div
                key={item.event_id}
                className="p-4 hover:bg-slate/20 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => setSelectedItem(item)}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-cloud">{item.event_type}</span>
                      <span className="text-xs font-mono text-ash bg-smoke/50 px-2 py-0.5 rounded">
                        {item.source}
                      </span>
                      <span className="text-xs font-mono text-pulse bg-pulse/10 px-2 py-0.5 rounded">
                        {item.retry_count} retries
                      </span>
                    </div>
                    <span className="text-xs font-mono text-ash">{item.event_id}</span>
                    {item.failure_reason && (
                      <p className="text-xs text-pulse mt-2 p-2 bg-pulse/5 rounded border border-pulse/20">
                        {item.failure_reason}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleRetry(item)}
                      className="p-2 rounded-lg bg-arc/10 border border-arc/30 text-arc hover:bg-arc/20 transition-colors"
                      title="Retry"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDismiss(item)}
                      className="p-2 rounded-lg bg-pulse/10 border border-pulse/30 text-pulse hover:bg-pulse/20 transition-colors"
                      title="Dismiss"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="text-xs text-ash mt-2">
                  Failed at {new Date(item.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {(offset > 0 || hasMore) && (
          <div className="flex items-center justify-between p-4 border-t border-smoke/20">
            <button
              onClick={() => fetchDLQ(Math.max(0, offset - limit))}
              disabled={offset === 0 || loading}
              className="flex items-center gap-1 text-sm text-arc hover:text-volt disabled:text-smoke disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <span className="text-xs font-mono text-ash">
              Showing {offset + 1} - {offset + items.length}
            </span>
            <button
              onClick={() => fetchDLQ(offset + limit)}
              disabled={!hasMore || loading}
              className="flex items-center gap-1 text-sm text-arc hover:text-volt disabled:text-smoke disabled:cursor-not-allowed transition-colors"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Item Detail Modal */}
      {selectedItem && (
        <DLQItemModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onRetry={handleRetry}
          onDismiss={handleDismiss}
        />
      )}
    </div>
  )
}

interface DLQItemModalProps {
  item: DLQItem
  onClose: () => void
  onRetry: (item: DLQItem) => void
  onDismiss: (item: DLQItem) => void
}

function DLQItemModal({ item, onClose, onRetry, onDismiss }: DLQItemModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-sm">
      <div className="bg-abyss border border-smoke/30 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-smoke/30">
          <h2 className="text-lg font-display font-semibold text-cloud flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-pulse" />
            Failed Event Details
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-smoke/30 rounded transition-colors">
            <X className="w-5 h-5 text-ash" />
          </button>
        </div>

        <div className="p-4 space-y-4 overflow-y-auto max-h-[60vh]">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono text-ash uppercase">Event ID</label>
              <p className="text-sm font-mono text-cloud mt-1">{item.event_id}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Retry Count</label>
              <p className="text-sm font-mono text-pulse mt-1">{item.retry_count}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Event Type</label>
              <p className="text-sm text-cloud mt-1">{item.event_type}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Source</label>
              <p className="text-sm text-cloud mt-1">{item.source}</p>
            </div>
            <div className="col-span-2">
              <label className="text-xs font-mono text-ash uppercase">Failed At</label>
              <p className="text-sm text-cloud mt-1">{new Date(item.created_at).toLocaleString()}</p>
            </div>
          </div>

          {item.failure_reason && (
            <div>
              <label className="text-xs font-mono text-ash uppercase">Failure Reason</label>
              <div className="mt-2 p-4 bg-pulse/10 border border-pulse/30 rounded-lg">
                <p className="text-sm text-pulse font-mono">{item.failure_reason}</p>
              </div>
            </div>
          )}

          <div>
            <label className="text-xs font-mono text-ash uppercase">Payload</label>
            <pre className="mt-2 p-4 bg-slate/50 rounded-lg text-xs font-mono text-cloud overflow-x-auto">
              {JSON.stringify(item.data, null, 2)}
            </pre>
          </div>
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
              onDismiss(item)
              onClose()
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-pulse/10 border border-pulse/30 text-pulse hover:bg-pulse/20 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span className="text-sm font-medium">Dismiss</span>
          </button>
          <button
            onClick={() => {
              onRetry(item)
              onClose()
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-arc/10 border border-arc/30 text-arc hover:bg-arc/20 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="text-sm font-medium">Retry</span>
          </button>
        </div>
      </div>
    </div>
  )
}

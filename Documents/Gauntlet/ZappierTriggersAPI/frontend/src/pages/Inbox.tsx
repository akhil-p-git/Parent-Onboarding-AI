import { useEffect, useState } from 'react'
import { api, InboxItem } from '../lib/api'
import { Inbox as InboxIcon, RefreshCw, Check, CheckCheck, Activity, X } from 'lucide-react'

export default function Inbox() {
  const [items, setItems] = useState<InboxItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [acknowledging, setAcknowledging] = useState(false)
  const [selectedItem, setSelectedItem] = useState<InboxItem | null>(null)

  const fetchInbox = async () => {
    setLoading(true)
    try {
      const response = await api.inbox.list({ limit: 50 })
      setItems(response.data)
      setSelected(new Set())
    } catch (err) {
      console.error('Failed to fetch inbox:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInbox()
  }, [])

  const toggleSelect = (receiptHandle: string) => {
    const newSelected = new Set(selected)
    if (newSelected.has(receiptHandle)) {
      newSelected.delete(receiptHandle)
    } else {
      newSelected.add(receiptHandle)
    }
    setSelected(newSelected)
  }

  const selectAll = () => {
    if (selected.size === items.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(items.map((i) => i.receipt_handle)))
    }
  }

  const acknowledgeSelected = async () => {
    if (selected.size === 0) return

    setAcknowledging(true)
    try {
      await api.inbox.acknowledge(Array.from(selected))
      fetchInbox()
    } catch (err) {
      console.error('Failed to acknowledge:', err)
    } finally {
      setAcknowledging(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-cloud">Inbox</h1>
          <p className="text-ash text-sm mt-1">Messages awaiting acknowledgment</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchInbox}
            className="p-2 rounded-lg bg-slate/50 border border-smoke/30 hover:border-smoke/50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 text-mist ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <InboxIcon className="w-4 h-4 text-arc" />
          <span className="text-sm font-mono text-mist">
            {items.length} message{items.length !== 1 ? 's' : ''}
          </span>
        </div>
        {selected.size > 0 && (
          <div className="flex items-center gap-4">
            <span className="text-sm text-volt">{selected.size} selected</span>
            <button
              onClick={acknowledgeSelected}
              disabled={acknowledging}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-volt/10 border border-volt/30 text-volt hover:bg-volt/20 transition-colors text-sm disabled:opacity-50"
            >
              <CheckCheck className="w-4 h-4" />
              {acknowledging ? 'Acknowledging...' : 'Acknowledge'}
            </button>
          </div>
        )}
      </div>

      {/* Inbox List */}
      <div className="bg-abyss/50 rounded-xl border border-smoke/30 overflow-hidden">
        {/* Header Row */}
        {items.length > 0 && (
          <div className="flex items-center gap-4 p-3 bg-slate/30 border-b border-smoke/20">
            <button
              onClick={selectAll}
              className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                selected.size === items.length && items.length > 0
                  ? 'bg-volt border-volt text-void'
                  : 'border-smoke/50 hover:border-volt/50'
              }`}
            >
              {selected.size === items.length && items.length > 0 && (
                <Check className="w-3 h-3" />
              )}
            </button>
            <span className="text-xs font-mono text-ash uppercase flex-1">Message</span>
            <span className="text-xs font-mono text-ash uppercase w-32">Received</span>
          </div>
        )}

        {loading && items.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <Activity className="w-6 h-6 text-volt animate-pulse" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-16">
            <InboxIcon className="w-10 h-10 text-smoke mx-auto mb-3" />
            <p className="text-ash">Inbox is empty</p>
            <p className="text-xs text-ash/60 mt-1">No messages awaiting acknowledgment</p>
          </div>
        ) : (
          <div className="divide-y divide-smoke/20">
            {items.map((item) => (
              <div
                key={item.receipt_handle}
                className="flex items-center gap-4 p-4 hover:bg-slate/20 transition-colors"
              >
                <button
                  onClick={() => toggleSelect(item.receipt_handle)}
                  className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                    selected.has(item.receipt_handle)
                      ? 'bg-volt border-volt text-void'
                      : 'border-smoke/50 hover:border-volt/50'
                  }`}
                >
                  {selected.has(item.receipt_handle) && <Check className="w-3 h-3" />}
                </button>

                <div
                  className="flex-1 cursor-pointer"
                  onClick={() => setSelectedItem(item)}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-cloud">{item.event_type}</span>
                    <span className="text-xs font-mono text-ash bg-smoke/50 px-2 py-0.5 rounded">
                      {item.source}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-ash">{item.event_id}</span>
                </div>

                <span className="text-xs font-mono text-ash w-32 text-right">
                  {new Date(item.received_at).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Item Detail Modal */}
      {selectedItem && (
        <InboxItemModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onAcknowledge={async () => {
            try {
              await api.inbox.acknowledge([selectedItem.receipt_handle])
              setSelectedItem(null)
              fetchInbox()
            } catch (err) {
              console.error('Failed to acknowledge:', err)
            }
          }}
        />
      )}
    </div>
  )
}

interface InboxItemModalProps {
  item: InboxItem
  onClose: () => void
  onAcknowledge: () => void
}

function InboxItemModal({ item, onClose, onAcknowledge }: InboxItemModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-void/80 backdrop-blur-sm">
      <div className="bg-abyss border border-smoke/30 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-smoke/30">
          <h2 className="text-lg font-display font-semibold text-cloud">Message Details</h2>
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
              <label className="text-xs font-mono text-ash uppercase">Event Type</label>
              <p className="text-sm text-cloud mt-1">{item.event_type}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Source</label>
              <p className="text-sm text-cloud mt-1">{item.source}</p>
            </div>
            <div>
              <label className="text-xs font-mono text-ash uppercase">Received</label>
              <p className="text-sm text-cloud mt-1">{new Date(item.received_at).toLocaleString()}</p>
            </div>
          </div>

          <div>
            <label className="text-xs font-mono text-ash uppercase">Payload</label>
            <pre className="mt-2 p-4 bg-slate/50 rounded-lg text-xs font-mono text-cloud overflow-x-auto">
              {JSON.stringify(item.data, null, 2)}
            </pre>
          </div>

          <div>
            <label className="text-xs font-mono text-ash uppercase">Receipt Handle</label>
            <p className="text-xs font-mono text-ash mt-1 break-all">{item.receipt_handle}</p>
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
            onClick={onAcknowledge}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-volt/10 border border-volt/30 text-volt hover:bg-volt/20 transition-colors"
          >
            <CheckCheck className="w-4 h-4" />
            <span className="text-sm font-medium">Acknowledge</span>
          </button>
        </div>
      </div>
    </div>
  )
}

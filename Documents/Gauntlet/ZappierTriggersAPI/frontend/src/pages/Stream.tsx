import { useEffect, useState, useRef } from 'react'
import { Radio, Pause, Play, Trash2, Activity, Zap } from 'lucide-react'

interface StreamEvent {
  id: string
  event_type: string
  source: string
  data: Record<string, unknown>
  timestamp: string
}

export default function Stream() {
  const [events, setEvents] = useState<StreamEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [paused, setPaused] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const eventsContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [])

  useEffect(() => {
    // Auto-scroll to bottom when new events arrive
    if (eventsContainerRef.current && !paused) {
      eventsContainerRef.current.scrollTop = eventsContainerRef.current.scrollHeight
    }
  }, [events, paused])

  const connect = () => {
    const apiBase = import.meta.env.VITE_API_URL || '/api/v1'
    const apiKey = localStorage.getItem('api_key') || ''

    // Close existing connection
    disconnect()

    const url = new URL(`${apiBase}/events/stream`, window.location.origin)
    if (apiKey) {
      url.searchParams.set('api_key', apiKey)
    }

    const eventSource = new EventSource(url.toString())

    eventSource.onopen = () => {
      setConnected(true)
    }

    eventSource.onerror = () => {
      setConnected(false)
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (!eventSourceRef.current) {
          connect()
        }
      }, 5000)
    }

    eventSource.onmessage = (e) => {
      if (paused) return

      try {
        const data = JSON.parse(e.data)

        // Handle heartbeat
        if (data.type === 'heartbeat') {
          return
        }

        const streamEvent: StreamEvent = {
          id: data.id || crypto.randomUUID(),
          event_type: data.event_type || 'unknown',
          source: data.source || 'unknown',
          data: data.data || data,
          timestamp: new Date().toISOString(),
        }

        setEvents((prev) => [...prev.slice(-99), streamEvent])
      } catch {
        // Ignore parse errors
      }
    }

    eventSourceRef.current = eventSource
  }

  const disconnect = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setConnected(false)
  }

  const togglePause = () => {
    setPaused(!paused)
  }

  const clearEvents = () => {
    setEvents([])
  }

  const getEventColor = (eventType: string) => {
    if (eventType.includes('error') || eventType.includes('fail')) {
      return 'border-pulse/50 bg-pulse/5'
    }
    if (eventType.includes('success') || eventType.includes('complete')) {
      return 'border-volt/50 bg-volt/5'
    }
    if (eventType.includes('warn')) {
      return 'border-spark/50 bg-spark/5'
    }
    return 'border-arc/50 bg-arc/5'
  }

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-display font-bold text-cloud flex items-center gap-3">
            <Radio className={`w-6 h-6 ${connected ? 'text-volt' : 'text-pulse'}`} />
            Live Stream
          </h1>
          <p className="text-ash text-sm mt-1">Real-time event feed via SSE</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
            connected
              ? 'border-volt/30 bg-volt/10'
              : 'border-pulse/30 bg-pulse/10'
          }`}>
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-volt blink' : 'bg-pulse'}`} />
            <span className={`text-xs font-mono ${connected ? 'text-volt' : 'text-pulse'}`}>
              {connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>

          {/* Controls */}
          <button
            onClick={togglePause}
            className={`p-2 rounded-lg border transition-colors ${
              paused
                ? 'bg-volt/10 border-volt/30 text-volt'
                : 'bg-slate/50 border-smoke/30 text-mist hover:border-smoke/50'
            }`}
            title={paused ? 'Resume' : 'Pause'}
          >
            {paused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </button>

          <button
            onClick={clearEvents}
            className="p-2 rounded-lg bg-slate/50 border border-smoke/30 text-mist hover:border-smoke/50 transition-colors"
            title="Clear"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          <button
            onClick={connected ? disconnect : connect}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              connected
                ? 'bg-pulse/10 border border-pulse/30 text-pulse hover:bg-pulse/20'
                : 'bg-volt/10 border border-volt/30 text-volt hover:bg-volt/20'
            }`}
          >
            {connected ? 'Disconnect' : 'Connect'}
          </button>
        </div>
      </div>

      {/* Event Counter */}
      <div className="flex items-center gap-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-arc" />
          <span className="text-sm font-mono text-mist">
            {events.length} event{events.length !== 1 ? 's' : ''}
          </span>
        </div>
        {paused && (
          <span className="text-xs font-mono text-spark bg-spark/10 border border-spark/30 px-2 py-1 rounded">
            PAUSED
          </span>
        )}
      </div>

      {/* Events Stream */}
      <div
        ref={eventsContainerRef}
        className="flex-1 bg-abyss/50 rounded-xl border border-smoke/30 overflow-y-auto"
      >
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <Radio className={`w-12 h-12 mb-4 ${connected ? 'text-volt animate-pulse' : 'text-smoke'}`} />
            <p className="text-ash mb-2">
              {connected ? 'Waiting for events...' : 'Not connected'}
            </p>
            <p className="text-xs text-ash/60">
              {connected
                ? 'Events will appear here as they are published'
                : 'Click Connect to start receiving events'}
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-2">
            {events.map((event, index) => (
              <div
                key={`${event.id}-${index}`}
                className={`p-3 rounded-lg border ${getEventColor(event.event_type)} slide-in`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-volt" />
                    <span className="font-medium text-cloud">{event.event_type}</span>
                    <span className="text-xs font-mono text-ash bg-smoke/50 px-2 py-0.5 rounded">
                      {event.source}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-ash">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <pre className="text-xs font-mono text-mist overflow-x-auto">
                  {JSON.stringify(event.data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="flex-shrink-0 text-center">
        <p className="text-xs text-ash">
          Events are stored locally and will be cleared on refresh
        </p>
      </div>
    </div>
  )
}

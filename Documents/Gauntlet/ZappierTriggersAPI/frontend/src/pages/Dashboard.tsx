import { useEffect, useState } from 'react'
import { api, Event, HealthStatus } from '../lib/api'
import { Activity, Zap, AlertTriangle, CheckCircle, Clock, TrendingUp } from 'lucide-react'

interface Stats {
  totalEvents: number
  pendingEvents: number
  deliveredEvents: number
  failedEvents: number
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [recentEvents, setRecentEvents] = useState<Event[]>([])
  const [stats, setStats] = useState<Stats>({
    totalEvents: 0,
    pendingEvents: 0,
    deliveredEvents: 0,
    failedEvents: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthData, eventsData] = await Promise.all([
          api.health(),
          api.events.list({ limit: 5 }),
        ])
        setHealth(healthData)
        setRecentEvents(eventsData.data)

        // Calculate stats from events
        const delivered = eventsData.data.filter(e => e.status === 'delivered').length
        const failed = eventsData.data.filter(e => e.status === 'failed').length
        const pending = eventsData.data.filter(e => e.status === 'pending' || e.status === 'processing').length

        setStats({
          totalEvents: eventsData.pagination.total || eventsData.data.length,
          pendingEvents: pending,
          deliveredEvents: delivered,
          failedEvents: failed,
        })
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'text-volt'
      case 'failed':
        return 'text-pulse'
      case 'processing':
        return 'text-arc'
      default:
        return 'text-spark'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
        return <CheckCircle className="w-4 h-4" />
      case 'failed':
        return <AlertTriangle className="w-4 h-4" />
      case 'processing':
        return <Activity className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Activity className="w-8 h-8 text-volt animate-pulse mx-auto mb-4" />
          <p className="text-mist font-mono text-sm">LOADING SYSTEMS...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-cloud">Dashboard</h1>
          <p className="text-ash text-sm mt-1">System overview and metrics</p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-volt blink' : 'bg-pulse'}`} />
          <span className="text-xs font-mono text-mist uppercase">
            {health?.status || 'unknown'}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total Events"
          value={stats.totalEvents}
          icon={<Zap className="w-5 h-5" />}
          color="volt"
        />
        <StatCard
          label="Pending"
          value={stats.pendingEvents}
          icon={<Clock className="w-5 h-5" />}
          color="spark"
        />
        <StatCard
          label="Delivered"
          value={stats.deliveredEvents}
          icon={<CheckCircle className="w-5 h-5" />}
          color="volt"
        />
        <StatCard
          label="Failed"
          value={stats.failedEvents}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="pulse"
        />
      </div>

      {/* System Components */}
      {health?.components && (
        <div className="bg-abyss/50 rounded-xl border border-smoke/30 p-6">
          <h2 className="text-lg font-display font-semibold text-cloud mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-arc" />
            System Components
          </h2>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(health.components).map(([name, status]) => (
              <div
                key={name}
                className="bg-slate/50 rounded-lg p-4 border border-smoke/30"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-mono text-mist uppercase">{name}</span>
                  <div className={`w-2 h-2 rounded-full ${status === 'healthy' ? 'bg-volt' : 'bg-pulse'} blink`} />
                </div>
                <span className={`text-sm font-medium ${status === 'healthy' ? 'text-volt' : 'text-pulse'}`}>
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Events */}
      <div className="bg-abyss/50 rounded-xl border border-smoke/30 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-display font-semibold text-cloud flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-volt" />
            Recent Events
          </h2>
          <a href="/events" className="text-sm text-arc hover:text-volt transition-colors">
            View all →
          </a>
        </div>

        {recentEvents.length === 0 ? (
          <div className="text-center py-8">
            <Zap className="w-8 h-8 text-smoke mx-auto mb-2" />
            <p className="text-ash text-sm">No events yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentEvents.map((event) => (
              <div
                key={event.id}
                className="flex items-center justify-between p-3 bg-slate/30 rounded-lg border border-smoke/20 hover:border-smoke/40 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className={`${getStatusColor(event.status)}`}>
                    {getStatusIcon(event.status)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-cloud">{event.event_type}</span>
                      <span className="text-xs font-mono text-ash bg-smoke/50 px-2 py-0.5 rounded">
                        {event.source}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-ash">
                      {event.id.slice(0, 8)}...
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-mono uppercase ${getStatusColor(event.status)}`}>
                    {event.status}
                  </span>
                  <p className="text-xs text-ash mt-1">
                    {new Date(event.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface StatCardProps {
  label: string
  value: number
  icon: React.ReactNode
  color: 'volt' | 'pulse' | 'arc' | 'spark'
}

function StatCard({ label, value, icon, color }: StatCardProps) {
  const colorClasses = {
    volt: 'text-volt bg-volt/10 border-volt/30',
    pulse: 'text-pulse bg-pulse/10 border-pulse/30',
    arc: 'text-arc bg-arc/10 border-arc/30',
    spark: 'text-spark bg-spark/10 border-spark/30',
  }

  const glowClasses = {
    volt: 'glow-volt',
    pulse: 'glow-pulse',
    arc: 'glow-arc',
    spark: '',
  }

  return (
    <div className={`rounded-xl border p-4 ${colorClasses[color]} ${glowClasses[color]}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-mono text-mist uppercase">{label}</span>
        {icon}
      </div>
      <p className="text-3xl font-mono font-bold">{value.toLocaleString()}</p>
    </div>
  )
}

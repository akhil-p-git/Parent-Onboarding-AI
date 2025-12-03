import { Outlet, NavLink } from 'react-router-dom'
import {
  Activity,
  Inbox,
  AlertTriangle,
  Radio,
  Zap,
  Settings,
  BarChart3
} from 'lucide-react'

const navItems = [
  { to: '/', icon: BarChart3, label: 'Dashboard' },
  { to: '/events', icon: Zap, label: 'Events' },
  { to: '/inbox', icon: Inbox, label: 'Inbox' },
  { to: '/dlq', icon: AlertTriangle, label: 'Dead Letter' },
  { to: '/stream', icon: Radio, label: 'Live Stream' },
]

export default function Layout() {
  return (
    <div className="min-h-screen bg-void grid-bg scanlines">
      {/* Top bar */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-abyss/90 backdrop-blur-md border-b border-smoke/50">
        <div className="flex items-center justify-between px-6 h-14">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-8 h-8 bg-volt/20 rounded-lg flex items-center justify-center glow-volt">
                <Activity className="w-5 h-5 text-volt" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-volt rounded-full blink" />
            </div>
            <div>
              <h1 className="font-display font-bold text-cloud tracking-tight">
                TRIGGERS
              </h1>
              <p className="text-[10px] text-ash font-mono -mt-1 tracking-widest">
                CONTROL ROOM
              </p>
            </div>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate/50 rounded-full border border-smoke/50">
              <div className="w-2 h-2 bg-volt rounded-full blink" />
              <span className="text-xs font-mono text-mist">SYSTEM ONLINE</span>
            </div>
            <button className="p-2 rounded-lg hover:bg-smoke/50 transition-colors">
              <Settings className="w-4 h-4 text-ash" />
            </button>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside className="fixed left-0 top-14 bottom-0 w-56 bg-abyss/50 border-r border-smoke/30 z-40">
        <nav className="p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                  isActive
                    ? 'bg-volt/10 text-volt border border-volt/30 glow-volt'
                    : 'text-mist hover:text-cloud hover:bg-smoke/30'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm font-medium">{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-smoke/30">
          <div className="bg-slate/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1.5 h-1.5 bg-arc rounded-full blink" />
              <span className="text-xs font-mono text-mist">API Status</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-lg font-mono font-bold text-volt">99.9</div>
                <div className="text-[10px] text-ash">UPTIME %</div>
              </div>
              <div>
                <div className="text-lg font-mono font-bold text-arc">24ms</div>
                <div className="text-[10px] text-ash">LATENCY</div>
              </div>
              <div>
                <div className="text-lg font-mono font-bold text-spark">1.2K</div>
                <div className="text-[10px] text-ash">REQ/S</div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="pl-56 pt-14">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

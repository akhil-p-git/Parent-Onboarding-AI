import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Events from './pages/Events'
import Inbox from './pages/Inbox'
import DLQ from './pages/DLQ'
import Stream from './pages/Stream'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="events" element={<Events />} />
          <Route path="inbox" element={<Inbox />} />
          <Route path="dlq" element={<DLQ />} />
          <Route path="stream" element={<Stream />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

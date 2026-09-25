import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Feed from './pages/Feed'
import Profile from './pages/Profile'
import Graph from './pages/Graph'

export default function App() {
  return (
    <BrowserRouter>
      <nav className="fixed top-0 inset-x-0 z-10 bg-white border-b border-gray-200 flex items-center gap-6 px-6 h-12">
        <Link to="/" className="font-semibold text-sm">감정의 계정들</Link>
        <Link to="/graph" className="text-sm text-gray-500 hover:text-black">그래프</Link>
      </nav>
      <main className="pt-12">
        <Routes>
          <Route path="/" element={<Feed />} />
          <Route path="/@:agentId" element={<Profile />} />
          <Route path="/graph" element={<Graph />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

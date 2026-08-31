import { Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import { AuthProvider, useAuth } from './services/auth.jsx'
import Dashboard from './pages/Dashboard.jsx'
import StateDetail from './pages/StateDetail.jsx'
import AnalyzePage from './pages/AnalyzePage.jsx'
import MyLocations from './pages/MyLocations.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import AlertsPage from './pages/AlertsPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import AboutPage from './pages/AboutPage.jsx'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="page container"><p className="muted">Loading…</p></div>
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <div className="app-shell">
        <Navbar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/state/:stateId" element={<StateDetail />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route
              path="/my-locations"
              element={<Protected><MyLocations /></Protected>}
            />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/alerts" element={<Protected><AlertsPage /></Protected>} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </AuthProvider>
  )
}

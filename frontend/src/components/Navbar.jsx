import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth.jsx'

const cls = ({ isActive }) => (isActive ? 'active' : '')

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand">⛰️ NER Landslide AI</Link>
      <div className="nav-links">
        <NavLink to="/" end className={cls}>Dashboard</NavLink>
        <NavLink to="/analyze" className={cls}>Analyze Location</NavLink>
        <NavLink to="/history" className={cls}>History</NavLink>
        {user && <NavLink to="/my-locations" className={cls}>My Locations</NavLink>}
        {user && <NavLink to="/alerts" className={cls}>Alerts</NavLink>}
        <NavLink to="/about" className={cls}>About</NavLink>
      </div>
      <div className="nav-auth">
        {user ? (
          <>
            <span className="nav-user">👤 {user.name}</span>
            <button className="btn btn-light btn-sm" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn btn-light btn-sm">Login</Link>
            <Link to="/register" className="btn btn-primary btn-sm">Register</Link>
          </>
        )}
      </div>
    </nav>
  )
}

import { createContext, useContext, useEffect, useState } from 'react'
import { api } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('ner_token')
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get('/api/auth/me')
      .then((d) => setUser(d.user))
      .catch(() => {
        localStorage.removeItem('ner_token')
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const d = await api.post('/api/auth/login', { email, password }, false)
    localStorage.setItem('ner_token', d.access_token)
    setUser(d.user)
    return d.user
  }

  const register = async (name, email, password, role = 'public') => {
    const d = await api.post('/api/auth/register', { name, email, password, role }, false)
    localStorage.setItem('ner_token', d.access_token)
    setUser(d.user)
    return d.user
  }

  const logout = () => {
    localStorage.removeItem('ner_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

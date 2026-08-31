import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth.jsx'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '', role: 'public' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await register(form.name, form.email, form.password, form.role)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page container">
      <h1>Create account</h1>
      <p className="subtitle">Free registration — save locations, configure alerts, revisit your history.</p>
      <form className="form" onSubmit={submit}>
        {error && <div className="form-error">{error}</div>}
        <div className="field">
          <label htmlFor="name">Full name</label>
          <input id="name" value={form.name} onChange={set('name')} required minLength={2} maxLength={120} />
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={form.email} onChange={set('email')} required />
        </div>
        <div className="field">
          <label htmlFor="password">Password (min 8 characters)</label>
          <input id="password" type="password" value={form.password} onChange={set('password')} required minLength={8} />
        </div>
        <div className="field">
          <label htmlFor="confirm">Confirm password</label>
          <input id="confirm" type="password" value={form.confirm} onChange={set('confirm')} required />
        </div>
        <div className="field">
          <label htmlFor="role">I am a…</label>
          <select id="role" value={form.role} onChange={set('role')}>
            <option value="public">General public / resident / traveller</option>
            <option value="authority">Government / disaster management authority</option>
            <option value="researcher">Researcher / student</option>
          </select>
        </div>
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Creating…' : 'Register'}
        </button>
        <p className="muted">Already have an account? <Link to="/login">Login</Link></p>
      </form>
    </div>
  )
}

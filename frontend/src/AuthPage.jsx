import { useState } from 'react'
import { signUp, logIn } from './authService'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function AuthPage({ onAuthed }) {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const isSignup = mode === 'signup'

  function validate() {
    if (!EMAIL_RE.test(email)) return 'Enter a valid email address.'
    if (password.length < 8) return 'Password needs at least 8 characters.'
    if (isSignup && password !== confirm) return "Passwords don't match."
    return ''
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setError('')
    setBusy(true)
    try {
      const session = isSignup ? await signUp(email, password) : await logIn(email, password)
      onAuthed(session)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function switchMode(next) {
    setMode(next)
    setError('')
    setPassword('')
    setConfirm('')
  }

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand__mark">
          <span className="dot" />
          INTAKE
        </div>
        <h1 className="auth-brand__title">
          Feed it the file.
          <br />
          Get back <em>the numbers.</em>
        </h1>
        <p className="auth-brand__tagline">
          A single intake point for the PDFs, spreadsheets, and photos coming off the floor —
          it reads them so nobody has to re-type them.
        </p>
      </div>

      <div className="auth-panel">
        <div className="auth-card">
          <div className="auth-tabs">
            <button
              type="button"
              className={`auth-tab${mode === 'login' ? ' auth-tab--active' : ''}`}
              onClick={() => switchMode('login')}
            >
              Sign in
            </button>
            <button
              type="button"
              className={`auth-tab${mode === 'signup' ? ' auth-tab--active' : ''}`}
              onClick={() => switchMode('signup')}
            >
              Create account
            </button>
          </div>

          <h2 className="auth-title">{isSignup ? 'Set up access.' : 'Welcome back.'}</h2>
          <p className="auth-sub">
            {isSignup
              ? 'One account, keeps your extraction history with it.'
              : 'Sign in to reach the intake queue.'}
          </p>

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <label className="auth-field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                placeholder="you@company.com"
              />
            </label>

            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                placeholder="••••••••"
              />
            </label>

            {isSignup && (
              <label className="auth-field">
                <span>Confirm password</span>
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  autoComplete="new-password"
                  placeholder="••••••••"
                />
              </label>
            )}

            {error && <p className="auth-error">{error}</p>}

            <button type="submit" className="auth-submit" disabled={busy}>
              {busy ? 'Checking…' : isSignup ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <p className="auth-footnote">
            {isSignup ? 'Already have an account?' : 'New here?'}{' '}
            <button
              type="button"
              className="auth-link"
              onClick={() => switchMode(isSignup ? 'login' : 'signup')}
            >
              {isSignup ? 'Sign in instead' : 'Create one'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

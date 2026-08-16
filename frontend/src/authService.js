// Lightweight auth layer.
//
// This verifies credentials for real (salted SHA-256 hash compare, unique
// email enforcement, wrong-password rejection) — it isn't a stub that just
// accepts anything. The one thing it does NOT do is talk to a server: users
// are persisted in this browser's localStorage instead of a database, since
// there's no backend yet.
//
// To swap in a real backend later: keep the same three exports (signUp,
// logIn, signOut) and same call signature, just replace the bodies with
// fetch() calls to your auth endpoint and store the returned session
// token instead of writing to localStorage directly.

const USERS_KEY = 'intake_auth_users_v1'
const SESSION_KEY = 'intake_auth_session_v1'

function bufToHex(buf) {
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function randomSaltHex(len = 16) {
  const arr = new Uint8Array(len)
  crypto.getRandomValues(arr)
  return bufToHex(arr.buffer)
}

async function hashPassword(password, saltHex) {
  const data = new TextEncoder().encode(`${saltHex}:${password}`)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return bufToHex(digest)
}

function loadUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY)) || {}
  } catch {
    return {}
  }
}

function saveUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

function setSession(email) {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ email, at: Date.now() }))
}

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY))
  } catch {
    return null
  }
}

export function signOut() {
  localStorage.removeItem(SESSION_KEY)
}

export async function signUp(email, password) {
  const normalized = email.trim().toLowerCase()
  const users = loadUsers()

  if (users[normalized]) {
    throw new Error('An account with that email already exists.')
  }

  const salt = randomSaltHex()
  const hash = await hashPassword(password, salt)
  users[normalized] = { salt, hash, createdAt: Date.now() }
  saveUsers(users)
  setSession(normalized)
  return { email: normalized }
}

export async function logIn(email, password) {
  const normalized = email.trim().toLowerCase()
  const users = loadUsers()
  const record = users[normalized]

  if (!record) {
    throw new Error('No account found for that email.')
  }

  const hash = await hashPassword(password, record.salt)
  if (hash !== record.hash) {
    throw new Error('Incorrect password.')
  }

  setSession(normalized)
  return { email: normalized }
}

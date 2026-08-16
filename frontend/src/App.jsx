import { useCallback, useRef, useState } from 'react'
import AuthPage from './AuthPage.jsx'
import { getSession, signOut } from './authService'

const BAYS = [
  {
    id: 'pdf',
    label: 'Bay 01',
    kind: 'PDF',
    formats: '.pdf',
    accept: '.pdf,application/pdf',
    hint: 'Spec sheets, reports, manifests',
  },
  {
    id: 'csv',
    label: 'Bay 02',
    kind: 'CSV',
    formats: '.csv, .xlsx',
    accept: '.csv,.xlsx,text/csv',
    hint: 'Sensor logs, inventory exports',
  },
  {
    id: 'image',
    label: 'Bay 03',
    kind: 'Image',
    formats: '.png, .jpg, .heic',
    accept: 'image/*',
    hint: 'Nameplates, gauges, labels',
  },
]

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Mock extraction — replace with a real API call once the backend endpoint exists.
function mockExtract(file, kind) {
  const byKind = {
    PDF: {
      doc_type: 'work_order',
      fields_found: 14,
      key_fields: { part_no: 'PN-2291-A', qty: 480, due: '2026-09-02' },
    },
    CSV: {
      doc_type: 'sensor_log',
      rows: 3120,
      key_fields: { avg_temp_c: 61.4, max_pressure_psi: 118, anomalies: 3 },
    },
    Image: {
      doc_type: 'nameplate',
      fields_found: 6,
      key_fields: { model: 'HX-4400', serial: 'SN774-201', voltage: '480V' },
    },
  }
  return byKind[kind]
}

function IntakeBay({ bay, onFiles }) {
  const [active, setActive] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault()
      setActive(false)
      onFiles(bay, Array.from(e.dataTransfer.files))
    },
    [bay, onFiles],
  )

  return (
    <div className={`bay${active ? ' bay--active' : ''}`}>
      <div className="bay__head">
        <span className="bay__label">{bay.label}</span>
      </div>
      <div className="bay__kind">{bay.kind}</div>
      <div
        className="bay__drop"
        onDragOver={(e) => {
          e.preventDefault()
          setActive(true)
        }}
        onDragLeave={() => setActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <span className="bay__corner-a" />
        <span className="bay__corner-b" />
        <p className="bay__drop-text">Drop file or click to browse</p>
        <p className="bay__formats">{bay.formats}</p>
        <input
          ref={inputRef}
          className="bay__input"
          type="file"
          accept={bay.accept}
          multiple
          onChange={(e) => {
            onFiles(bay, Array.from(e.target.files))
            e.target.value = ''
          }}
        />
      </div>
      <p className="bay__formats" style={{ marginTop: 10, color: 'var(--steel)' }}>
        {bay.hint}
      </p>
    </div>
  )
}

function Tag({ item, onRemove }) {
  const statusLabel = {
    queued: 'Queued',
    extracting: 'Extracting…',
    done: 'Extracted',
  }[item.status]

  return (
    <div>
      <div className="tag">
        <span className="tag__hole" />
        <div>
          <div className="tag__name">{item.file.name}</div>
          <div className="tag__meta">
            {item.kind} · {formatSize(item.file.size)}
          </div>
        </div>
        <span className={`tag__status tag__status--${item.status}`}>{statusLabel}</span>
        <button className="tag__remove" onClick={() => onRemove(item.uid)} aria-label="Remove">
          ×
        </button>
      </div>
      {item.status === 'done' && (
        <div className="result">
          <strong>{item.result.doc_type}</strong>
          {'\n'}
          {JSON.stringify(item.result.key_fields, null, 2)}
        </div>
      )}
    </div>
  )
}

function IntakePage({ session, onSignOut }) {
  const [queue, setQueue] = useState([])

  const handleFiles = useCallback((bay, files) => {
    if (!files.length) return
    const items = files.map((file) => ({
      uid: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      file,
      kind: bay.kind,
      status: 'queued',
      result: null,
    }))
    setQueue((q) => [...items, ...q])

    items.forEach((item) => {
      const t1 = setTimeout(() => {
        setQueue((q) => q.map((it) => (it.uid === item.uid ? { ...it, status: 'extracting' } : it)))
      }, 350)
      const t2 = setTimeout(() => {
        setQueue((q) =>
          q.map((it) =>
            it.uid === item.uid
              ? { ...it, status: 'done', result: mockExtract(item.file, item.kind) }
              : it,
          ),
        )
      }, 1500)
      return () => {
        clearTimeout(t1)
        clearTimeout(t2)
      }
    })
  }, [])

  const removeItem = useCallback((uid) => {
    setQueue((q) => q.filter((it) => it.uid !== uid))
  }, [])

  return (
    <div className="page">
      <div className="topbar">
        <div className="topbar__mark">
          <span className="dot" />
          INTAKE / EXTRACTION SYSTEM
        </div>
        <nav className="topbar__nav">
          <span>{session.email}</span>
          <button className="btn-ghost" onClick={onSignOut} style={{ marginLeft: 4 }}>
            Sign out
          </button>
        </nav>
      </div>

      <div className="hero">
        <div className="hero__eyebrow">File Intake — v0.1</div>
        <h1 className="hero__title">
          Feed it the file.
          <br />
          Get back <em>the numbers.</em>
        </h1>
        <p className="hero__sub">
          Drop a PDF, spreadsheet, or photo from the floor and this pulls out the fields that
          matter — part numbers, readings, quantities — no manual re-typing.
        </p>
      </div>

      <div className="bays">
        {BAYS.map((bay) => (
          <IntakeBay key={bay.id} bay={bay} onFiles={handleFiles} />
        ))}
      </div>

      <div className="queue">
        <div className="queue__head">
          <span className="queue__title">Queue</span>
          <span className="queue__count">{queue.length} tagged</span>
        </div>

        {queue.length === 0 ? (
          <div className="queue__empty">No files tagged yet — drop one into a bay above.</div>
        ) : (
          queue.map((item) => <Tag key={item.uid} item={item} onRemove={removeItem} />)
        )}
      </div>

      <div className="footer">
        <span>UNIHACK — FILE INTAKE</span>
        <span>MOCK MODE — NOT CONNECTED TO EXTRACTION API</span>
      </div>
    </div>
  )
}

export default function App() {
  const [session, setSession] = useState(() => getSession())

  if (!session) {
    return <AuthPage onAuthed={setSession} />
  }

  return (
    <IntakePage
      session={session}
      onSignOut={() => {
        signOut()
        setSession(null)
      }}
    />
  )
}

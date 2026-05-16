export default function BottomNav({ page, setPage }) {
  const items = [
    { key: 'chat',    label: 'Чат',     icon: <ChatIcon /> },
    { key: 'history', label: 'История', icon: <HistoryIcon /> },
    { key: 'profile', label: 'Профиль', icon: <ProfileIcon /> },
    { key: 'plans',   label: 'Тарифы',  icon: <PlansIcon /> },
  ]

  return (
    <nav className="bottom-nav">
      {items.map(it => (
        <button
          key={it.key}
          className={`nav-item${page === it.key ? ' active' : ''}`}
          onClick={() => setPage(it.key)}
        >
          {it.icon}
          <span className="nav-label">{it.label}</span>
        </button>
      ))}
    </nav>
  )
}

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
  )
}

function HistoryIcon() {
  return (
    <svg viewBox="0 0 24 24"><path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.95-2.05L6.7 18.29A8.94 8.94 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
  )
}

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>
  )
}

function PlansIcon() {
  return (
    <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/></svg>
  )
}

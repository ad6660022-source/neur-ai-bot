import { useState, useEffect } from 'react'
import { api } from './api.js'
import BottomNav    from './components/BottomNav.jsx'
import ChatPage     from './pages/ChatPage.jsx'
import HistoryPage  from './pages/HistoryPage.jsx'
import ProfilePage  from './pages/ProfilePage.jsx'
import PlansPage    from './pages/PlansPage.jsx'

const tg = window.Telegram?.WebApp

export default function App() {
  const [page,    setPage]    = useState('chat')
  const [user,    setUser]    = useState(null)
  const [authErr, setAuthErr] = useState(false)

  // Preloaded chat state from HistoryPage → ChatPage
  const [loadedChat, setLoadedChat] = useState(null)

  useEffect(() => {
    api.me()
      .then(data => setUser(data.user))
      .catch(() => setAuthErr(true))
  }, [])

  const handleLoadChat = ({ model, messages }) => {
    setLoadedChat({ model, messages })
    setPage('chat')
  }

  const refreshUser = () => {
    api.me().then(data => setUser(data.user)).catch(() => {})
  }

  if (authErr) {
    return (
      <div className="app" style={{ alignItems: 'center', justifyContent: 'center', gap: 12 }}>
        <div style={{ fontSize: 40 }}>⚠️</div>
        <div className="fw-bold">Ошибка авторизации</div>
        <div className="text-hint" style={{ textAlign: 'center', padding: '0 32px' }}>
          Открой этот раздел через Telegram — нельзя открывать напрямую в браузере.
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="app" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div className="loader">
          <span /><span /><span />
        </div>
      </div>
    )
  }

  const renderPage = () => {
    switch (page) {
      case 'chat':
        return (
          <ChatPage
            user={user}
            setPage={setPage}
            loadedChat={loadedChat}
            clearLoadedChat={() => setLoadedChat(null)}
          />
        )
      case 'history':
        return <HistoryPage user={user} onLoadChat={handleLoadChat} />
      case 'profile':
        return <ProfilePage user={user} setPage={setPage} />
      case 'plans':
        return <PlansPage user={user} />
      default:
        return null
    }
  }

  return (
    <div className="app">
      {renderPage()}
      <BottomNav page={page} setPage={(p) => { setPage(p); if (p === 'profile') refreshUser() }} />
    </div>
  )
}

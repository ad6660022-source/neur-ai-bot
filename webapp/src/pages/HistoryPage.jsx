import { useState, useEffect } from 'react'
import { api } from '../api.js'

const MODEL_EMOJI = { chatgpt: '🟢', claude: '🟣' }

export default function HistoryPage({ user, onLoadChat }) {
  const [chats,   setChats]   = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [deleting, setDeleting] = useState(null)

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.chatsList()
      setChats(data.chats || [])
    } catch (err) {
      setError(err.message || 'Не удалось загрузить историю')
    } finally {
      setLoading(false)
    }
  }

  const del = async (id, e) => {
    e.stopPropagation()
    if (deleting) return
    setDeleting(id)
    try {
      await api.chatDelete(id)
      setChats(prev => prev.filter(c => c.id !== id))
    } catch {
      // silent
    } finally {
      setDeleting(null)
    }
  }

  const open = async (chat) => {
    try {
      const data = await api.chatLoad(chat.id)
      onLoadChat({ model: chat.model, messages: data.messages || [] })
    } catch {
      // silent
    }
  }

  const fmt = (iso) => {
    if (!iso) return ''
    const d = new Date(iso)
    const now = new Date()
    const diff = now - d
    if (diff < 86400000) {
      return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    }
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
  }

  const plan = user?.plan || 'free'
  const canSave = plan !== 'free'

  if (!canSave) {
    return (
      <div className="page">
        <div className="header">
          <div className="header-title">История</div>
        </div>
        <div className="empty">
          <div className="empty-icon">💾</div>
          <div className="fw-bold">Сохранение недоступно</div>
          <div className="text-hint">Для сохранения чатов нужен тариф Basic или выше</div>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="header">
        <div className="header-title">История чатов</div>
        <div className="header-subtitle">{chats.length} сохранённых</div>
      </div>

      {loading && (
        <div className="empty">
          <div className="loader" style={{ alignSelf: 'center' }}>
            <span /><span /><span />
          </div>
        </div>
      )}

      {error && <div className="banner error">{error}</div>}

      {!loading && !error && chats.length === 0 && (
        <div className="empty">
          <div className="empty-icon">📭</div>
          <div className="fw-bold">Нет сохранённых чатов</div>
          <div className="text-hint">Нажми 💾 в чате чтобы сохранить диалог</div>
        </div>
      )}

      {chats.map(chat => (
        <div
          key={chat.id}
          className="chat-item"
          onClick={() => open(chat)}
        >
          <div className="chat-icon">
            {MODEL_EMOJI[chat.model] || '🤖'}
          </div>
          <div className="chat-info">
            <div className="chat-name">{chat.name || 'Чат'}</div>
            <div className="chat-meta">
              {chat.model === 'chatgpt' ? 'ChatGPT' : 'Claude'} · {fmt(chat.created_at)}
            </div>
          </div>
          <button
            className="delete-btn"
            onClick={(e) => del(chat.id, e)}
            disabled={deleting === chat.id}
          >
            {deleting === chat.id ? '...' : '🗑'}
          </button>
        </div>
      ))}
    </div>
  )
}

import { useState, useRef, useEffect } from 'react'
import { api, markdownToHtml } from '../api.js'

const MODELS = [
  { key: 'chatgpt', label: 'ChatGPT', emoji: '🟢' },
  { key: 'claude',  label: 'Claude',  emoji: '🟣' },
]

export default function ChatPage({ user, setPage, loadedChat, clearLoadedChat }) {
  const [model,    setModel]    = useState('chatgpt')
  const [messages, setMessages] = useState([])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [toast,    setToast]    = useState(null)
  const bottomRef  = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (loadedChat) {
      setModel(loadedChat.model || 'chatgpt')
      setMessages(loadedChat.messages || [])
      setError(null)
      clearLoadedChat?.()
    }
  }, [loadedChat])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const plan = user?.plan || 'free'

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setError(null)

    const userMsg = { role: 'user', content: text }
    const newHistory = [...messages, userMsg]
    setMessages(newHistory)
    setLoading(true)

    try {
      const data = await api.chat({ model, messages: newHistory, mode: 'default' })
      setMessages([...newHistory, { role: 'assistant', content: data.response }])
    } catch (err) {
      if (err.error === 'limit_reached') {
        setError({ type: 'limit', msg: err.message })
      } else if (err.error === 'model_unavailable') {
        setError({ type: 'unavailable', msg: err.message })
      } else {
        setError({ type: 'error', msg: err.message || 'Ошибка. Попробуй ещё раз.' })
      }
      setMessages(newHistory.slice(0, -1)) // revert
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
    showToast('Чат очищен')
  }

  const saveChat = async () => {
    if (messages.length < 2) { showToast('Нечего сохранять'); return }
    try {
      const first = messages.find(m => m.role === 'user')?.content || 'Чат'
      await api.chatSave({ name: first.slice(0, 60), model, mode: 'default', history: messages })
      showToast('✅ Чат сохранён')
    } catch {
      showToast('Ошибка при сохранении')
    }
  }

  const modelLocked = model === 'claude' && (user?.usage?.claude?.limit_monthly === 0)

  return (
    <div className="page">
      {/* Header */}
      <div className="header">
        <div>
          <div className="header-title">🤖 NEUR AI</div>
          <div className="header-subtitle">
            {plan.toUpperCase()} · {user?.bonus_requests > 0 ? `+${user.bonus_requests} бонус` : ''}
          </div>
        </div>
        {messages.length > 0 && (
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-sm btn-secondary" onClick={saveChat}>💾</button>
            <button className="btn btn-sm btn-secondary" onClick={clearChat}>🗑</button>
          </div>
        )}
      </div>

      {/* Model tabs */}
      <div className="model-tabs">
        {MODELS.map(m => (
          <button
            key={m.key}
            className={`model-tab${model === m.key ? ' active' : ''}`}
            onClick={() => { setModel(m.key); setError(null) }}
          >
            {m.emoji} {m.label}
          </button>
        ))}
      </div>

      {/* Error banner */}
      {error && (
        <div className={`banner ${error.type === 'limit' ? 'limit' : 'error'}`}>
          {error.msg}
          {error.type === 'limit' && (
            <div className="mt-8">
              <button className="btn btn-sm btn-primary mt-8" onClick={() => setPage('plans')}>
                Посмотреть тарифы →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Unavailable model notice */}
      {modelLocked && (
        <div className="banner limit">
          Claude доступен только с тарифами Pro и Ultra.
          <div className="mt-8">
            <button className="btn btn-sm btn-primary" onClick={() => setPage('plans')}>
              Обновить тариф →
            </button>
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.length === 0 && !error && (
        <div className="empty">
          <div className="empty-icon">{MODELS.find(m => m.key === model)?.emoji}</div>
          <div className="fw-bold">
            {model === 'chatgpt' ? 'ChatGPT (GPT-4o)' : 'Claude (Sonnet 4.6)'}
          </div>
          <div className="text-hint">Напиши любой вопрос для начала диалога</div>
        </div>
      )}

      <div className="messages">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}
        {loading && (
          <div className="loader">
            <span /><span /><span />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input — extra padding for the fixed input bar */}
      <div style={{ height: 70 }} />

      {/* Fixed input bar */}
      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Напиши сообщение..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          rows={1}
          disabled={loading || modelLocked}
        />
        <button className="send-btn" onClick={send} disabled={!input.trim() || loading || modelLocked}>
          <svg viewBox="0 0 24 24"><path d="M2 21L23 12 2 3v7l15 2-15 2v7z"/></svg>
        </button>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  const html = isUser ? null : markdownToHtml(msg.content)
  return (
    <div className={`message ${isUser ? 'user' : 'ai'}`}>
      {isUser
        ? msg.content
        : <span dangerouslySetInnerHTML={{ __html: html }} />
      }
    </div>
  )
}

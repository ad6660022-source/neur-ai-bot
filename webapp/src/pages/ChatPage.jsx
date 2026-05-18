import { useState, useRef, useEffect } from 'react'
import { api, parseMarkdown } from '../api.js'

const MODELS = [
  { key: 'chatgpt', label: 'ChatGPT', emoji: '🟢' },
  { key: 'claude',  label: 'Claude',  emoji: '🟣' },
]

const RECENT_KEY = 'neur_recent_chat'

export default function ChatPage({ user, setPage, loadedChat, clearLoadedChat }) {
  const [model,    setModel]    = useState('chatgpt')
  const [messages, setMessages] = useState([])
  const [input,    setInput]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [toast,    setToast]    = useState(null)
  const bottomRef   = useRef(null)
  const textareaRef = useRef(null)

  // Restore from loadedChat (history) or localStorage (auto-save)
  useEffect(() => {
    if (loadedChat) {
      setModel(loadedChat.model || 'chatgpt')
      setMessages(loadedChat.messages || [])
      setError(null)
      clearLoadedChat?.()
      return
    }
    try {
      const raw = localStorage.getItem(RECENT_KEY)
      if (raw) {
        const { model: m, messages: msgs } = JSON.parse(raw)
        if (Array.isArray(msgs) && msgs.length > 0) {
          setModel(m || 'chatgpt')
          setMessages(msgs)
        }
      }
    } catch {}
  }, [loadedChat])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const plan = user?.plan || 'free'

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  const autoSave = (mdl, msgs) => {
    try {
      localStorage.setItem(RECENT_KEY, JSON.stringify({ model: mdl, messages: msgs }))
    } catch {}
  }

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    setError(null)

    const userMsg = { role: 'user', content: text }
    const newHistory = [...messages, userMsg]
    setMessages(newHistory)
    setLoading(true)

    try {
      const data = await api.chat({ model, messages: newHistory, mode: 'default' })
      const updated = [...newHistory, { role: 'assistant', content: data.response }]
      setMessages(updated)
      autoSave(model, updated)
    } catch (err) {
      if (err.error === 'limit_reached') {
        setError({ type: 'limit', msg: err.message })
      } else if (err.error === 'model_unavailable') {
        setError({ type: 'unavailable', msg: err.message })
      } else {
        setError({ type: 'error', msg: err.message || 'Ошибка. Попробуй ещё раз.' })
      }
      setMessages(newHistory.slice(0, -1))
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

  const handleInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
    try { localStorage.removeItem(RECENT_KEY) } catch {}
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

  const switchModel = (key) => {
    setModel(key)
    setError(null)
    autoSave(key, messages)
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
            onClick={() => switchModel(m.key)}
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

      {/* Empty state */}
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

      <div style={{ height: 70 }} />

      {/* Fixed input bar */}
      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Напиши сообщение..."
          value={input}
          onChange={handleInput}
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

// ─── Message component ────────────────────────────────────────────────────

function Message({ msg }) {
  const isUser = msg.role === 'user'
  if (isUser) {
    return <div className="message user">{msg.content}</div>
  }
  const parts = parseMarkdown(msg.content)
  return (
    <div className="message ai">
      {parts.map((part, i) =>
        part.type === 'code'
          ? <CodeBlock key={i} code={part.code} lang={part.lang} />
          : <span key={i} dangerouslySetInnerHTML={{ __html: part.html }} />
      )}
    </div>
  )
}

function CodeBlock({ code, lang }) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard?.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <div className="code-block">
      <div className="code-header">
        {lang && <span className="code-lang">{lang}</span>}
        <button className="copy-btn" onClick={copy}>
          {copied ? '✓ Скопировано' : 'Копировать'}
        </button>
      </div>
      <pre><code>{code}</code></pre>
    </div>
  )
}

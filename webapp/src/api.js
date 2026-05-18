const tg = window.Telegram?.WebApp
const initData = tg?.initData || ''

async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `tma ${initData}`,
      ...options.headers,
    },
  })
  const data = await res.json()
  if (!res.ok || data.error) throw data
  return data
}

export const api = {
  me:           ()         => request('/me'),
  plans:        ()         => request('/plans'),
  chat:         (body)     => request('/chat', { method: 'POST', body: JSON.stringify(body) }),
  chatsList:    ()         => request('/chats'),
  chatLoad:     (id)       => request(`/chats/${id}`),
  chatSave:     (body)     => request('/chats', { method: 'POST', body: JSON.stringify(body) }),
  chatDelete:   (id)       => request(`/chats/${id}`, { method: 'DELETE' }),
  createInvoice:(plan)     => request('/invoice', { method: 'POST', body: JSON.stringify({ plan }) }),
}

// ─── Markdown parser ──────────────────────────────────────────────────────

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

function textToHtml(text) {
  let t = escapeHtml(text)
  t = t.replace(/`([^`\n]+)`/g, (_, c) => `<code>${escapeHtml(c)}</code>`)
  t = t.replace(/\*\*(.+?)\*\*/gs, '<b>$1</b>')
  t = t.replace(/\*(.+?)\*/gs, '$1')
  t = t.replace(/__(.+?)__/gs, '$1')
  t = t.replace(/_(.+?)_/gs, '$1')
  t = t.replace(/^#{1,6}\s+/gm, '')
  t = t.replace(/\n/g, '<br>')
  return t
}

// Returns [{type:'text', html}, {type:'code', lang, code}]
export function parseMarkdown(text) {
  if (!text) return []
  const parts = []
  let last = 0
  const re = /```(\w*)\n?([\s\S]*?)```/g
  let m
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      parts.push({ type: 'text', html: textToHtml(text.slice(last, m.index)) })
    }
    parts.push({ type: 'code', lang: m[1] || '', code: m[2].trim() })
    last = re.lastIndex
  }
  if (last < text.length) {
    parts.push({ type: 'text', html: textToHtml(text.slice(last)) })
  }
  return parts
}

// Legacy helper
export function markdownToHtml(text) {
  return parseMarkdown(text)
    .map(p => p.type === 'code'
      ? `<pre><code>${escapeHtml(p.code)}</code></pre>`
      : p.html)
    .join('')
}

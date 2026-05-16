import { useState } from 'react'
import { api } from '../api.js'

const tg = window.Telegram?.WebApp

const PLANS = [
  {
    key: 'free',
    name: 'Бесплатный',
    price: null,
    features: [
      '🟢 ChatGPT: 20/мес · 5/день',
      '🟣 Claude: недоступен',
      '💾 Сохранение чатов: нет',
    ],
  },
  {
    key: 'basic',
    name: 'Basic',
    price: '99 ⭐',
    stars: 99,
    features: [
      '🟢 ChatGPT: 100/мес · 20/день',
      '🟣 Claude: недоступен',
      '💾 Сохранение чатов: 5',
    ],
  },
  {
    key: 'pro',
    name: 'Pro',
    price: '399 ⭐',
    stars: 399,
    featured: true,
    features: [
      '🟢 ChatGPT: 250/мес · 40/день',
      '🟣 Claude: 60/мес · 10/день',
      '💾 Сохранение чатов: 30',
    ],
  },
  {
    key: 'ultra',
    name: 'Ultra',
    price: '999 ⭐',
    stars: 999,
    features: [
      '🟢 ChatGPT: 700/мес · 100/день',
      '🟣 Claude: 180/мес · 25/день',
      '💾 Сохранение чатов: ∞',
    ],
  },
]

export default function PlansPage({ user }) {
  const [loading, setLoading] = useState(null)
  const [error, setError]     = useState(null)
  const currentPlan = user?.plan || 'free'

  const buy = async (planKey) => {
    if (loading) return
    setLoading(planKey)
    setError(null)
    try {
      const data = await api.createInvoice(planKey)
      if (tg?.openInvoice) {
        tg.openInvoice(data.invoice_link, (status) => {
          if (status === 'paid') {
            tg.showAlert('Оплата прошла! Перезапусти бота для обновления тарифа.')
          }
        })
      } else {
        window.open(data.invoice_link, '_blank')
      }
    } catch (err) {
      setError(err.message || 'Ошибка при создании счёта')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="page">
      <div className="header">
        <div>
          <div className="header-title">Тарифы</div>
          <div className="header-subtitle">Оплата звёздами Telegram ⭐</div>
        </div>
      </div>

      {error && (
        <div className="banner error">{error}</div>
      )}

      {PLANS.map(plan => {
        const isCurrent = plan.key === currentPlan
        const isUpgrade = !isCurrent && plan.stars > 0
        const cardClass = `plan-card${isCurrent ? ' current' : ''}${plan.featured ? ' featured' : ''}`

        return (
          <div className={cardClass} key={plan.key}>
            {isCurrent && <div className="current-badge">Текущий</div>}
            {plan.featured && !isCurrent && (
              <div className="current-badge" style={{ background: '#ffd60a', color: '#000' }}>
                Популярный
              </div>
            )}
            <div className="plan-name">{plan.name}</div>
            <div className="plan-price">{plan.price ?? 'Бесплатно'}</div>
            <ul className="plan-features">
              {plan.features.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
            {isUpgrade && (
              <button
                className="btn btn-primary"
                onClick={() => buy(plan.key)}
                disabled={!!loading}
              >
                {loading === plan.key ? 'Открываем...' : `Купить за ${plan.price}`}
              </button>
            )}
            {isCurrent && plan.key !== 'free' && (
              <div style={{ fontSize: 13, color: 'var(--hint)', textAlign: 'center', marginTop: 4 }}>
                Активна до: {user?.subscription_end
                  ? new Date(user.subscription_end).toLocaleDateString('ru-RU')
                  : '—'}
              </div>
            )}
          </div>
        )
      })}

      <div style={{ padding: '4px 16px 24px', fontSize: 13, color: 'var(--hint)', textAlign: 'center', lineHeight: 1.6 }}>
        Оплата через Telegram Stars — безопасно и мгновенно.
        После оплаты тариф активируется автоматически.
      </div>
    </div>
  )
}

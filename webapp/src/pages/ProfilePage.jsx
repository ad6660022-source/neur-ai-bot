import { useState, useEffect } from 'react'
import { api } from '../api.js'

export default function ProfilePage({ user, setPage }) {
  const plan = user?.plan || 'free'
  const usage = user?.usage || {}
  const bonus = user?.bonus_requests || 0

  const PLAN_LABELS = { free: 'Бесплатный', basic: 'Basic', pro: 'Pro', ultra: 'Ultra' }
  const PLAN_EMOJIS = { free: '⚪', basic: '🔵', pro: '🟡', ultra: '🔴' }

  const models = [
    { key: 'chatgpt', label: 'ChatGPT', emoji: '🟢' },
    { key: 'claude',  label: 'Claude',  emoji: '🟣' },
  ]

  return (
    <div className="page">
      <div className="profile-header">
        <div className="avatar">👤</div>
        <div className="fw-bold" style={{ fontSize: 17 }}>
          {user?.first_name || 'Пользователь'}
        </div>
        <div className="plan-badge">
          {PLAN_EMOJIS[plan]} {PLAN_LABELS[plan]}
        </div>
        {bonus > 0 && (
          <div style={{ fontSize: 13, color: 'var(--success)' }}>
            +{bonus} бонусных запросов
          </div>
        )}
      </div>

      <div className="section-title">Использование запросов</div>
      {models.map(m => {
        const u = usage[m.key] || {}
        const monthly = u.used_monthly ?? 0
        const monthlyLimit = u.limit_monthly ?? 0
        const daily = u.used_daily ?? 0
        const dailyLimit = u.limit_daily ?? 0

        if (monthlyLimit === 0 && plan !== 'ultra') {
          return (
            <div className="card" key={m.key}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span className="fw-bold">{m.emoji} {m.label}</span>
                <span className="text-hint" style={{ fontSize: 13 }}>Недоступен</span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: '0%' }} />
              </div>
            </div>
          )
        }

        const monthlyPct = monthlyLimit === -1 ? 0 : Math.min(100, (monthly / monthlyLimit) * 100)
        const dailyPct   = dailyLimit === -1   ? 0 : Math.min(100, (daily   / dailyLimit)   * 100)
        const fillClass  = monthlyPct >= 90 ? 'danger' : monthlyPct >= 70 ? 'warning' : ''
        const unlim      = monthlyLimit === -1

        return (
          <div className="card" key={m.key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span className="fw-bold">{m.emoji} {m.label}</span>
              <span style={{ fontSize: 13, color: 'var(--hint)' }}>
                {unlim ? '∞' : `${monthly} / ${monthlyLimit}`} в месяц
              </span>
            </div>
            {!unlim && (
              <div className="progress-bar">
                <div className={`progress-fill ${fillClass}`} style={{ width: `${monthlyPct}%` }} />
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, marginBottom: 4 }}>
              <span style={{ fontSize: 12, color: 'var(--hint)' }}>Сегодня</span>
              <span style={{ fontSize: 12, color: 'var(--hint)' }}>
                {dailyLimit === -1 ? '∞' : `${daily} / ${dailyLimit}`}
              </span>
            </div>
            {dailyLimit !== -1 && (
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${dailyPct}%` }} />
              </div>
            )}
          </div>
        )
      })}

      <div className="section-title">Подписка</div>
      <div className="card">
        <div className="stat-row">
          <span className="stat-label">Текущий тариф</span>
          <span className="stat-value">{PLAN_EMOJIS[plan]} {PLAN_LABELS[plan]}</span>
        </div>
        {user?.subscription_end && (
          <div className="stat-row">
            <span className="stat-label">Действует до</span>
            <span className="stat-value">
              {new Date(user.subscription_end).toLocaleDateString('ru-RU')}
            </span>
          </div>
        )}
        {bonus > 0 && (
          <div className="stat-row">
            <span className="stat-label">Бонусные запросы</span>
            <span className="stat-value text-success">+{bonus}</span>
          </div>
        )}
      </div>

      {plan !== 'ultra' && (
        <div style={{ padding: '8px 16px 24px' }}>
          <button className="btn btn-primary" onClick={() => setPage('plans')}>
            Улучшить тариф →
          </button>
        </div>
      )}
    </div>
  )
}

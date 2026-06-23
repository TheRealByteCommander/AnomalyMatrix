import { useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import { useI18n } from '../i18n/I18nProvider';
import { login } from '../services';

export default function LoginPage({ onSuccess }) {
  const { t } = useI18n();
  const [userId, setUserId] = useState('admin-1');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await login(userId.trim(), password);
      onSuccess(data.user);
    } catch (err) {
      setError(err.message || t('login.failed'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <form className="card login-card" onSubmit={handleSubmit} data-testid="login-form">
        <p className="eyebrow">{t('login.eyebrow')}</p>
        <h2>{t('login.title')}</h2>
        <p className="muted">{t('login.hint')}</p>
        <label>
          {t('login.userId')}
          <input
            data-testid="login-user"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label>
          {t('login.password')}
          <input
            data-testid="login-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error ? <StatusBadge state="red">{error}</StatusBadge> : null}
        <button type="submit" className="tab active" data-testid="login-submit" disabled={loading}>
          {loading ? t('login.submitting') : t('login.submit')}
        </button>
      </form>
    </div>
  );
}

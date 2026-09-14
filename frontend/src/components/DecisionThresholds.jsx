import { useEffect, useState } from 'react';
import ContextHelp from './ContextHelp';
import { updateRecipeThresholds } from '../services';
import { useI18n } from '../i18n/I18nProvider';

export default function DecisionThresholds({
  recipe,
  canWrite = false,
  openHelp,
  onRecipeChange,
}) {
  const { t } = useI18n();
  const recipeId = recipe?.recipe_id || 'recipe-default';
  const current = recipe?.decision_thresholds || { amber: 0.55, red: 0.85 };
  const [amber, setAmber] = useState(current.amber ?? 0.55);
  const [red, setRed] = useState(current.red ?? 0.85);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);

  useEffect(() => {
    setAmber(current.amber ?? 0.55);
    setRed(current.red ?? 0.85);
  }, [recipeId, current.amber, current.red]);

  async function handleSave(e) {
    e.preventDefault();
    if (!canWrite) return;
    setBusy(true);
    setNotice(null);
    try {
      const saved = await updateRecipeThresholds(recipeId, { amber: Number(amber), red: Number(red) });
      onRecipeChange?.(saved);
      setNotice({ ok: true, message: t('thresholds.saved') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('thresholds.failed') });
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="card" data-testid="decision-thresholds">
      <h3>{t('thresholds.title')}</h3>
      <p className="muted">{t('thresholds.hint')}</p>
      <ContextHelp articleId="decision-colors" onOpen={openHelp} />
      <form className="training-form" onSubmit={handleSave}>
        <label>
          {t('thresholds.amber')}
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={amber}
            disabled={!canWrite || busy}
            onChange={(e) => setAmber(e.target.value)}
          />
        </label>
        <label>
          {t('thresholds.red')}
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={red}
            disabled={!canWrite || busy}
            onChange={(e) => setRed(e.target.value)}
          />
        </label>
        {canWrite ? (
          <button type="submit" className="primary" disabled={busy} data-testid="thresholds-save">
            {busy ? t('thresholds.saving') : t('thresholds.save')}
          </button>
        ) : (
          <p className="muted">{t('thresholds.readOnly')}</p>
        )}
      </form>
      {notice ? (
        <p className={notice.ok ? 'ok' : 'error'} role="status">
          {notice.message}
        </p>
      ) : null}
    </article>
  );
}

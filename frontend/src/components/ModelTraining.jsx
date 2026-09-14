import { useCallback, useEffect, useMemo, useState } from 'react';
import ContextHelp from './ContextHelp';
import StatusBadge from './StatusBadge';
import {
  activateModel,
  captureTrainingSamples,
  fetchModels,
  promoteModel,
  rollbackModel,
  trainModel,
} from '../services';
import { useI18n } from '../i18n/I18nProvider';

function statusState(status) {
  if (status === 'active') return 'green';
  if (status === 'candidate') return 'amber';
  return 'red';
}

function metaOf(model) {
  return model?.metadata || {};
}

function formatWhen(value, locale) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(locale === 'de' ? 'de-DE' : 'en-GB');
}

export default function ModelTraining({
  recipes = [],
  selectedCameraId = '',
  canTrain = false,
  canPromote = false,
  openHelp,
  onModelsChange,
}) {
  const { t, locale } = useI18n();
  const [models, setModels] = useState([]);
  const [active, setActive] = useState(null);
  const [memoryBank, setMemoryBank] = useState(null);
  const [samples, setSamples] = useState({ count: 0, recipe_id: 'recipe-default' });
  const [recipeId, setRecipeId] = useState('recipe-default');
  const [captureCount, setCaptureCount] = useState(8);
  const [sampleCount, setSampleCount] = useState(12);
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);

  const load = useCallback(async () => {
    const data = await fetchModels(recipeId);
    const items = data.items || [];
    setModels(items);
    setActive(data.active || items.find((m) => m.status === 'active') || items[0] || null);
    setMemoryBank(data.memory_bank || null);
    setSamples(data.training_samples || { count: 0, recipe_id: recipeId });
    onModelsChange?.(items);
    return data;
  }, [onModelsChange, recipeId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) {
          setNotice({ ok: false, message: err.message || t('training.loadFailed') });
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, t]);

  useEffect(() => {
    const first = recipes.find((r) => r.active === true || r.status === 'active') || recipes[0];
    if (first?.recipe_id) setRecipeId(first.recipe_id);
  }, [recipes]);

  async function runAction(key, fn, successKey, vars) {
    setBusy(key);
    setNotice(null);
    try {
      const result = await fn();
      await load();
      setNotice({ ok: true, message: t(successKey, vars) });
      return result;
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('training.actionFailed') });
      return null;
    } finally {
      setBusy('');
    }
  }

  const bankLoaded = Boolean(memoryBank?.loaded);
  const canWrite = canTrain || canPromote;
  const recipeOptions = recipes.length ? recipes : [{ recipe_id: recipeId, name: recipeId }];

  const rows = useMemo(
    () =>
      models.map((model) => {
        const meta = metaOf(model);
        return {
          ...model,
          recipe: meta.recipe_id || '—',
          sampleCount: meta.sample_count ?? meta.embedding_count ?? '—',
          dataSource: meta.data_source || '—',
          embeddings: meta.embedding_count ?? '—',
          artifact: meta.artifact_uri || '—',
        };
      }),
    [models]
  );

  return (
    <article className="card" data-testid="training-panel">
      <h3>{t('training.title')}</h3>
      <p className="muted">{t('training.hint')}</p>
      <ContextHelp articleId="good-part-training" onOpen={openHelp} />

      <div className="kpi-grid training-status">
        <div>
          <label>{t('training.activeModel')}</label>
          <strong>{active?.name || active?.model_id || t('training.none')}</strong>
          <p className="muted">{active?.model_version || '—'}</p>
        </div>
        <div>
          <label>{t('training.bankStatus')}</label>
          <StatusBadge state={bankLoaded ? 'green' : 'amber'}>
            {bankLoaded ? t('training.bankLoaded') : t('training.bankFallback')}
          </StatusBadge>
          <p className="muted">{memoryBank?.path || t('training.bankMissing')}</p>
        </div>
        <div>
          <label>{t('training.samplesOnDisk')}</label>
          <strong>{samples.count ?? 0}</strong>
          <p className="muted">{samples.recipe_id || recipeId}</p>
        </div>
        <div>
          <label>{t('training.camera')}</label>
          <strong>{selectedCameraId || t('training.cameraDefault')}</strong>
        </div>
      </div>

      <div className="training-form">
        <label>
          {t('training.recipe')}
          <select
            value={recipeId}
            onChange={(e) => setRecipeId(e.target.value)}
            disabled={Boolean(busy)}
          >
            {recipeOptions.map((recipe) => (
              <option key={recipe.recipe_id} value={recipe.recipe_id}>
                {recipe.name || recipe.recipe_id}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t('training.captureCount')}
          <input
            type="number"
            min={1}
            max={32}
            value={captureCount}
            disabled={!canTrain || Boolean(busy)}
            onChange={(e) => setCaptureCount(Number(e.target.value) || 1)}
          />
        </label>
        <label>
          {t('training.sampleCount')}
          <input
            type="number"
            min={3}
            max={64}
            value={sampleCount}
            disabled={!canTrain || Boolean(busy)}
            onChange={(e) => setSampleCount(Number(e.target.value) || 3)}
          />
        </label>
      </div>

      {canWrite ? (
        <div className="training-actions">
          {canTrain ? (
            <>
              <button
                type="button"
                className="tab active"
                data-testid="training-capture"
                disabled={Boolean(busy)}
                onClick={() =>
                  runAction(
                    'capture',
                    () =>
                      captureTrainingSamples({
                        recipeId,
                        cameraId: selectedCameraId || undefined,
                        count: captureCount,
                      }),
                    'training.captured',
                    { count: captureCount }
                  )
                }
              >
                {busy === 'capture' ? t('training.capturing') : t('training.capture')}
              </button>
              <button
                type="button"
                className="tab active"
                data-testid="training-start"
                disabled={Boolean(busy)}
                onClick={() =>
                  runAction(
                    'train',
                    () => trainModel({ recipeId, sampleCount }),
                    'training.trained'
                  )
                }
              >
                {busy === 'train' ? t('training.training') : t('training.train')}
              </button>
            </>
          ) : null}
          {canPromote ? (
            <button
              type="button"
              className="tab"
              data-testid="training-rollback"
              disabled={Boolean(busy)}
              onClick={() => runAction('rollback', () => rollbackModel(), 'training.rolledBack')}
            >
              {busy === 'rollback' ? t('training.rollingBack') : t('training.rollback')}
            </button>
          ) : null}
        </div>
      ) : (
        <p className="muted">{t('training.readOnly')}</p>
      )}

      {notice ? (
        <p className={notice.ok ? 'ok' : 'error'} role="status" data-testid="training-notice">
          {notice.message}
        </p>
      ) : null}

      <h4 className="training-history-title">{t('training.historyTitle')}</h4>
      <p className="muted">{t('training.historyHint')}</p>
      {!rows.length ? (
        <p className="muted">{t('training.historyEmpty')}</p>
      ) : (
        <div className="training-table" data-testid="training-history">
          <div className="training-row training-head">
            <span>{t('training.colModel')}</span>
            <span>{t('training.colRecipe')}</span>
            <span>{t('training.colCreated')}</span>
            <span>{t('training.colSamples')}</span>
            <span>{t('training.colSource')}</span>
            <span>{t('training.colStatus')}</span>
            <span>{t('training.colActions')}</span>
          </div>
          {rows.map((row) => {
            const isActive = row.status === 'active';
            const canActivate = canPromote && !isActive;
            const canPromoteRow = canPromote && row.status === 'candidate';
            return (
              <div key={row.model_id} className="training-row">
                <span>
                  <strong>{row.model_id}</strong>
                  <span className="muted"> {row.model_version}</span>
                </span>
                <span>{row.recipe}</span>
                <span>{formatWhen(row.created_at, locale)}</span>
                <span>
                  {row.sampleCount}
                  {row.embeddings !== '—' ? ` / ${row.embeddings}` : ''}
                </span>
                <span>{row.dataSource}</span>
                <span>
                  <StatusBadge state={statusState(row.status)}>
                    {t(`training.status.${row.status}`) !== `training.status.${row.status}`
                      ? t(`training.status.${row.status}`)
                      : row.status}
                  </StatusBadge>
                </span>
                <span className="training-row-actions">
                  {canPromoteRow ? (
                    <button
                      type="button"
                      className="tab"
                      data-testid={`training-promote-${row.model_id}`}
                      disabled={Boolean(busy)}
                      onClick={() =>
                        runAction(
                          `promote-${row.model_id}`,
                          () => promoteModel(row.model_id),
                          'training.promoted',
                          { id: row.model_id }
                        )
                      }
                    >
                      {t('training.promote')}
                    </button>
                  ) : null}
                  {canActivate ? (
                    <button
                      type="button"
                      className="tab"
                      data-testid={`training-activate-${row.model_id}`}
                      disabled={Boolean(busy)}
                      onClick={() =>
                        runAction(
                          `activate-${row.model_id}`,
                          () => activateModel(row.model_id),
                          'training.activated',
                          { id: row.model_id }
                        )
                      }
                    >
                      {t('training.activate')}
                    </button>
                  ) : (
                    <span className="muted">{isActive ? t('training.current') : ''}</span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

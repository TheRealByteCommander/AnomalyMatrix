import { useEffect, useMemo, useState } from 'react';
import ContextHelp from './ContextHelp';
import StatusBadge from './StatusBadge';
import { createRecipe, deleteRecipe, updateRecipe } from '../services';
import { useI18n } from '../i18n/I18nProvider';

const EMPTY_FORM = {
  recipe_id: '',
  name: '',
  recipe_version: 'v1',
  active: false,
  camera_id: '',
  exposure_ms: 10,
  gain_db: 2,
  amber: 0.55,
  red: 0.85,
};

function slugifyRecipeId(name) {
  const slug = String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
  if (!slug) return '';
  return slug.startsWith('recipe-') ? slug : `recipe-${slug}`;
}

function formFromRecipe(recipe) {
  if (!recipe) return { ...EMPTY_FORM };
  const camera = recipe.camera_profile || {};
  const lighting = recipe.lighting_profile || {};
  const thresholds = recipe.decision_thresholds || {};
  return {
    recipe_id: recipe.recipe_id || '',
    name: recipe.name || '',
    recipe_version: recipe.recipe_version || 'v1',
    active: Boolean(recipe.active),
    camera_id: camera.camera_id || '',
    exposure_ms: camera.exposure_ms ?? 10,
    gain_db: lighting.gain_db ?? 2,
    amber: thresholds.amber ?? 0.55,
    red: thresholds.red ?? 0.85,
  };
}

function payloadFromForm(form) {
  return {
    name: form.name.trim(),
    recipe_version: form.recipe_version.trim() || 'v1',
    active: Boolean(form.active),
    camera_profile: {
      camera_id: String(form.camera_id || '').trim(),
      exposure_ms: Number(form.exposure_ms) || 0,
    },
    lighting_profile: {
      gain_db: Number(form.gain_db) || 0,
    },
    decision_thresholds: {
      amber: Number(form.amber),
      red: Number(form.red),
    },
  };
}

export default function RecipeManager({
  recipes = [],
  selectedRecipeId,
  onSelect,
  onRecipesChange,
  canWrite = false,
  openHelp,
}) {
  const { t } = useI18n();
  const [mode, setMode] = useState('edit');
  const [form, setForm] = useState(EMPTY_FORM);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [deleteStep, setDeleteStep] = useState(0);
  const [deleteTyped, setDeleteTyped] = useState('');

  const selected = useMemo(
    () => recipes.find((item) => item.recipe_id === selectedRecipeId) || recipes[0] || null,
    [recipes, selectedRecipeId]
  );

  useEffect(() => {
    if (mode === 'create') return;
    setForm(formFromRecipe(selected));
  }, [selected, mode]);

  useEffect(() => {
    if (!deleteStep) return undefined;
    function onKey(e) {
      if (e.key === 'Escape') {
        e.preventDefault();
        setDeleteStep(0);
        setDeleteTyped('');
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [deleteStep]);

  function patchForm(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setNotice(null);
  }

  function startCreate() {
    setMode('create');
    setForm({ ...EMPTY_FORM });
    setNotice(null);
    setDeleteStep(0);
  }

  function selectRecipe(recipeId) {
    setMode('edit');
    setDeleteStep(0);
    setNotice(null);
    onSelect?.(recipeId);
  }

  async function handleSave(e) {
    e.preventDefault();
    if (!canWrite) return;
    setBusy(true);
    setNotice(null);
    try {
      const payload = payloadFromForm(form);
      let saved;
      if (mode === 'create') {
        const recipeId = form.recipe_id.trim() || slugifyRecipeId(form.name);
        saved = await createRecipe({ recipe_id: recipeId, ...payload });
        onRecipesChange?.(saved, 'create');
        selectRecipe(saved.recipe_id);
        setNotice({ ok: true, message: t('recipes.created') });
      } else {
        const recipeId = selected?.recipe_id;
        if (!recipeId) return;
        saved = await updateRecipe(recipeId, payload);
        onRecipesChange?.(saved, 'update');
        setNotice({ ok: true, message: t('recipes.updated') });
      }
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('recipes.saveFailed') });
    } finally {
      setBusy(false);
    }
  }

  function closeDelete() {
    setDeleteStep(0);
    setDeleteTyped('');
  }

  async function handleDeleteFinal() {
    const recipeId = selected?.recipe_id;
    if (!canWrite || !recipeId || selected?.protected) return;
    if (deleteTyped.trim() !== recipeId) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await deleteRecipe(recipeId, { confirm: true, confirmRecipeId: recipeId });
      onRecipesChange?.(result, 'delete');
      closeDelete();
      setNotice({ ok: true, message: t('recipes.deleted') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('recipes.deleteFailed') });
    } finally {
      setBusy(false);
    }
  }

  const protectedSelected = Boolean(selected?.protected || selected?.recipe_id === 'recipe-default');
  const deleteEnabled = canWrite && mode === 'edit' && selected && !protectedSelected;

  return (
    <article className="card" data-testid="recipe-manager">
      <h3>{t('recipes.title')}</h3>
      <p className="muted">{t('recipes.hint')}</p>
      <ContextHelp articleId="configuration-overview" onOpen={openHelp} />

      {!recipes.length ? (
        <p className="muted">{t('recipes.empty')}</p>
      ) : (
        <ul className="recipe-list">
          {recipes.map((recipe) => {
            const active = recipe.recipe_id === (selected?.recipe_id || selectedRecipeId);
            return (
              <li key={recipe.recipe_id}>
                <button
                  type="button"
                  className={active ? 'recipe-list-item active' : 'recipe-list-item'}
                  data-testid={`recipe-row-${recipe.recipe_id}`}
                  onClick={() => selectRecipe(recipe.recipe_id)}
                >
                  <span>
                    <strong>{recipe.name || recipe.recipe_id}</strong>
                    <span className="muted"> · {recipe.recipe_id} · {recipe.recipe_version}</span>
                  </span>
                  <StatusBadge state={recipe.active ? 'green' : 'amber'}>
                    {recipe.active ? t('recipes.active') : t('recipes.inactive')}
                  </StatusBadge>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {canWrite ? (
        <div className="training-actions">
          <button type="button" className="tab" data-testid="recipe-new" onClick={startCreate} disabled={busy}>
            {t('recipes.new')}
          </button>
        </div>
      ) : (
        <p className="muted">{t('recipes.readOnly')}</p>
      )}

      <form className="training-form" onSubmit={handleSave}>
        {mode === 'create' ? (
          <label>
            {t('recipes.id')}
            <input
              value={form.recipe_id}
              disabled={!canWrite || busy}
              placeholder={slugifyRecipeId(form.name) || 'recipe-…'}
              onChange={(e) => patchForm('recipe_id', e.target.value)}
              data-testid="recipe-id-input"
            />
          </label>
        ) : (
          <label>
            {t('recipes.id')}
            <input value={form.recipe_id} disabled readOnly />
          </label>
        )}
        <label>
          {t('recipes.name')}
          <input
            value={form.name}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('name', e.target.value)}
            data-testid="recipe-name-input"
            required={canWrite}
          />
        </label>
        <label>
          {t('recipes.version')}
          <input
            value={form.recipe_version}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('recipe_version', e.target.value)}
          />
        </label>
        <label className="recipe-checkbox">
          <input
            type="checkbox"
            checked={form.active}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('active', e.target.checked)}
          />
          {t('recipes.setActive')}
        </label>
        <label>
          {t('recipes.cameraId')}
          <input
            value={form.camera_id}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('camera_id', e.target.value)}
            placeholder="cam-01"
          />
        </label>
        <label>
          {t('recipes.exposure')}
          <input
            type="number"
            min={0}
            step={0.1}
            value={form.exposure_ms}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('exposure_ms', e.target.value)}
          />
        </label>
        <label>
          {t('recipes.gain')}
          <input
            type="number"
            step={0.1}
            value={form.gain_db}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('gain_db', e.target.value)}
          />
        </label>
        <label>
          {t('thresholds.amber')}
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={form.amber}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('amber', e.target.value)}
          />
        </label>
        <label>
          {t('thresholds.red')}
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={form.red}
            disabled={!canWrite || busy}
            onChange={(e) => patchForm('red', e.target.value)}
          />
        </label>
        {canWrite ? (
          <button type="submit" className="primary" disabled={busy} data-testid="recipe-save">
            {busy ? t('recipes.saving') : mode === 'create' ? t('recipes.create') : t('recipes.save')}
          </button>
        ) : null}
      </form>

      {deleteEnabled ? (
        <button
          type="button"
          className="danger"
          data-testid="recipe-delete"
          disabled={busy}
          onClick={() => {
            setDeleteTyped('');
            setDeleteStep(1);
          }}
        >
          {t('recipes.delete')}
        </button>
      ) : null}
      {canWrite && protectedSelected && mode === 'edit' ? (
        <p className="muted">{t('recipes.protectedHint')}</p>
      ) : null}

      {notice ? (
        <p className={notice.ok ? 'ok' : 'error'} role="status">
          {notice.message}
        </p>
      ) : null}

      {deleteStep > 0 ? (
        <div className="confirm-overlay" role="presentation" onClick={closeDelete}>
          <div
            className="confirm-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="recipe-delete-title"
            data-testid={`recipe-delete-step-${deleteStep}`}
            onClick={(e) => e.stopPropagation()}
          >
            {deleteStep === 1 ? (
              <>
                <h3 id="recipe-delete-title">{t('recipes.confirm1Title')}</h3>
                <p>{t('recipes.confirm1Body', { name: selected?.name || selected?.recipe_id })}</p>
                <div className="training-actions">
                  <button type="button" className="tab" onClick={closeDelete}>
                    {t('common.close')}
                  </button>
                  <button
                    type="button"
                    className="danger"
                    data-testid="recipe-delete-confirm-1"
                    onClick={() => setDeleteStep(2)}
                  >
                    {t('recipes.confirm1Action')}
                  </button>
                </div>
              </>
            ) : (
              <>
                <h3 id="recipe-delete-title">{t('recipes.confirm2Title')}</h3>
                <p>{t('recipes.confirm2Body', { id: selected?.recipe_id })}</p>
                <label>
                  {t('recipes.confirm2Label')}
                  <input
                    value={deleteTyped}
                    onChange={(e) => setDeleteTyped(e.target.value)}
                    data-testid="recipe-delete-type"
                    autoFocus
                  />
                </label>
                <div className="training-actions">
                  <button type="button" className="tab" onClick={closeDelete}>
                    {t('common.close')}
                  </button>
                  <button
                    type="button"
                    className="danger"
                    data-testid="recipe-delete-confirm-2"
                    disabled={busy || deleteTyped.trim() !== selected?.recipe_id}
                    onClick={handleDeleteFinal}
                  >
                    {busy ? t('recipes.deleting') : t('recipes.confirm2Action')}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      ) : null}
    </article>
  );
}

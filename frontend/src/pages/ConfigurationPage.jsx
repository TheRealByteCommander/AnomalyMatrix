import { useEffect, useMemo, useState } from 'react';
import { configSummary } from '../data/sampleData';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import {
  fetchAuthMe,
  fetchCameras,
  fetchLicenseStatus,
  fetchModels,
  fetchRecipes,
  saveCameraSelection,
} from '../services';
import { useI18n } from '../i18n/I18nProvider';

const MIN_CAMERAS = 1;
const MAX_CAMERAS = 4;

export default function ConfigurationPage({ openHelp }) {
  const { t } = useI18n();
  const [license, setLicense] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [models, setModels] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [selected, setSelected] = useState([]);
  const [driver, setDriver] = useState('');
  const [canConfigure, setCanConfigure] = useState(false);
  const [saveState, setSaveState] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [lic, recipeData, modelData, cameraData, me] = await Promise.all([
          fetchLicenseStatus(),
          fetchRecipes().catch(() => ({ items: [] })),
          fetchModels().catch(() => ({ items: [] })),
          fetchCameras().catch(() => ({ cameras: [], selection: { camera_ids: [] } })),
          fetchAuthMe().catch(() => null),
        ]);
        if (cancelled) return;
        setLicense(lic);
        setRecipes(recipeData.items || []);
        setModels(modelData.items || []);
        setCameras(cameraData.cameras || []);
        setDriver(cameraData.driver || '');
        const initial =
          cameraData.selection?.camera_ids?.length
            ? cameraData.selection.camera_ids
            : (cameraData.cameras || []).filter((c) => c.selected).map((c) => c.camera_id);
        setSelected(initial.slice(0, MAX_CAMERAS));
        const role = me?.role_id || me?.role || '';
        setCanConfigure(role === 'admin' || role === 'process_engineer');
      } catch {
        if (!cancelled) setLicense(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const licenseState = license?.active ? 'green' : 'amber';
  const activeRecipe = recipes.find((r) => r.active === true || r.status === 'active') || recipes[0];
  const activeModel = models.find((m) => m.status === 'active' || m.active === true) || models[0];

  const selectionValid = selected.length >= MIN_CAMERAS && selected.length <= MAX_CAMERAS;

  function toggleCamera(cameraId) {
    setSaveState(null);
    setSelected((prev) => {
      if (prev.includes(cameraId)) {
        if (prev.length <= MIN_CAMERAS) return prev;
        return prev.filter((id) => id !== cameraId);
      }
      if (prev.length >= MAX_CAMERAS) return prev;
      return [...prev, cameraId];
    });
  }

  async function handleSave() {
    if (!selectionValid || !canConfigure) return;
    setSaving(true);
    setSaveState(null);
    try {
      const saved = await saveCameraSelection(selected);
      setSelected(saved.camera_ids || selected);
      setSaveState({ ok: true, message: t('configuration.camerasSaved') });
    } catch (err) {
      setSaveState({ ok: false, message: err.message || t('configuration.camerasSaveFailed') });
    } finally {
      setSaving(false);
    }
  }

  const selectedLabels = useMemo(() => {
    const map = Object.fromEntries(cameras.map((c) => [c.camera_id, c.label || c.camera_id]));
    return selected.map((id) => map[id] || id).join(', ');
  }, [cameras, selected]);

  return (
    <section className="page-grid">
      <article className="card hero">
        <div>
          <p className="eyebrow">{t('configuration.eyebrow')}</p>
          <h2>{t('configuration.title')}</h2>
          <p className="muted">{t('configuration.hint')}</p>
          <ContextHelp articleId="configuration-overview" onOpen={openHelp} />
        </div>
        <StatusBadge state="green">{t('common.configValid')}</StatusBadge>
      </article>
      <article className="card kpi-grid">
        <div><label>{t('configuration.opcProfile')}</label><strong>{configSummary.opcUaProfile}</strong></div>
        <div><label>{t('configuration.recipeVersion')}</label><strong>{activeRecipe?.recipe_version || configSummary.recipeVersion}</strong></div>
        <div><label>{t('configuration.modelProfile')}</label><strong>{activeModel?.name || configSummary.modelProfile}</strong></div>
        <div><label>{t('configuration.auditMode')}</label><strong>{configSummary.auditMode}</strong></div>
      </article>
      <article className="card kpi-grid">
        <div><label>{t('configuration.licenseTier')}</label><strong>{license?.tier || t('license.na')}</strong></div>
        <div><label>{t('configuration.licenseActive')}</label><strong>{license ? String(license.active) : t('license.unknown')}</strong></div>
        <div><label>{t('configuration.graceActive')}</label><strong>{license ? String(license.grace_active) : t('license.unknown')}</strong></div>
        <div>
          <label>{t('configuration.status')}</label>
          <StatusBadge state={licenseState}>{license?.active ? t('license.licensed') : t('license.unlicensed')}</StatusBadge>
        </div>
      </article>

      <article className="card">
        <h3>{t('configuration.camerasTitle')}</h3>
        <p className="muted">
          {t('configuration.camerasHint', { min: MIN_CAMERAS, max: MAX_CAMERAS })}
          {driver ? ` · ${t('configuration.camerasDriver')}: ${driver}` : ''}
        </p>
        {!cameras.length ? (
          <p className="muted">{t('configuration.camerasEmpty')}</p>
        ) : (
          <ul className="camera-select-list">
            {cameras.map((cam) => {
              const checked = selected.includes(cam.camera_id);
              const disabled =
                !canConfigure ||
                (!checked && selected.length >= MAX_CAMERAS) ||
                (checked && selected.length <= MIN_CAMERAS);
              return (
                <li key={cam.camera_id}>
                  <label className={!cam.available ? 'muted' : undefined}>
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={disabled || cam.available === false}
                      onChange={() => toggleCamera(cam.camera_id)}
                    />
                    <span>
                      <strong>{cam.label || cam.camera_id}</strong>
                      <span className="muted">
                        {' '}
                        ({cam.camera_id}
                        {cam.source ? ` → ${cam.source}` : ''}
                        {cam.available === false ? ` · ${t('configuration.camerasUnavailable')}` : ''})
                      </span>
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        )}
        <p className="muted">
          {t('configuration.camerasSelected')}: {selected.length}/{MAX_CAMERAS}
          {selectedLabels ? ` — ${selectedLabels}` : ''}
        </p>
        {canConfigure ? (
          <button type="button" className="primary" disabled={!selectionValid || saving} onClick={handleSave}>
            {saving ? t('configuration.camerasSaving') : t('configuration.camerasSave')}
          </button>
        ) : (
          <p className="muted">{t('configuration.camerasReadOnly')}</p>
        )}
        {saveState && (
          <p className={saveState.ok ? 'ok' : 'error'} role="status">
            {saveState.message}
          </p>
        )}
      </article>
    </section>
  );
}

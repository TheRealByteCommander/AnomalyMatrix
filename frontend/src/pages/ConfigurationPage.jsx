import { useCallback, useEffect, useMemo, useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import {
  fetchAuthMe,
  fetchCameras,
  fetchLicenseStatus,
  fetchRecipes,
  saveCameraSelection,
} from '../services';
import { resolveRecipeSelection } from '../recipeSelection';
import LicenseBilling from '../components/LicenseBilling';
import DecisionThresholds from '../components/DecisionThresholds';
import RecipeManager from '../components/RecipeManager';
import StationVisionSetup from '../components/StationVisionSetup';
import StorageEndurancePanel from '../components/StorageEndurancePanel';
import { useI18n } from '../i18n/I18nProvider';
import { SETTINGS_ITEMS } from '../i18n/screens';

const MIN_CAMERAS = 1;

export default function ConfigurationPage({
  openHelp,
  goTo,
  selectedRecipeId = '',
  setSelectedRecipeId = () => {},
  settingsSection = '',
  setSettingsSection = () => {},
}) {
  const { t } = useI18n();
  const [license, setLicense] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [selected, setSelected] = useState([]);
  const [maxCameras, setMaxCameras] = useState(4);
  const [driver, setDriver] = useState('');
  const [canConfigure, setCanConfigure] = useState(false);
  const [canManageLicense, setCanManageLicense] = useState(false);
  const [canWriteRecipes, setCanWriteRecipes] = useState(false);
  const [saveState, setSaveState] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [lic, recipeData, cameraData, me] = await Promise.all([
          fetchLicenseStatus(),
          fetchRecipes().catch(() => ({ items: [] })),
          fetchCameras().catch(() => ({ cameras: [], selection: { camera_ids: [] } })),
          fetchAuthMe().catch(() => null),
        ]);
        if (cancelled) return;
        setLicense(lic);
        setRecipes(recipeData.items || []);
        const items = recipeData.items || [];
        if (items.length) {
          setSelectedRecipeId((prev) => resolveRecipeSelection(items, prev));
        }
        setCameras(cameraData.cameras || []);
        setDriver(cameraData.driver || '');
        setMaxCameras(cameraData.max_selectable || 4);
        const initial =
          cameraData.selection?.camera_ids?.length
            ? cameraData.selection.camera_ids
            : (cameraData.cameras || []).filter((c) => c.selected).map((c) => c.camera_id);
        setSelected(initial.slice(0, cameraData.max_selectable || 4));
        const role = me?.role_id || me?.role || '';
        const permissions = Array.isArray(me?.permissions) ? me.permissions : null;
        setCanConfigure(role === 'admin' || role === 'process_engineer');
        setCanManageLicense(role === 'admin');
        setCanWriteRecipes(permissions ? permissions.includes('recipes.write') : role === 'admin' || role === 'process_engineer');
      } catch {
        if (!cancelled) setLicense(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setSelectedRecipeId]);

  const selectedRecipe =
    recipes.find((r) => r.recipe_id === selectedRecipeId) ||
    recipes.find((r) => r.active === true || r.status === 'active') ||
    recipes[0];
  const activeRecipe = recipes.find((r) => r.active === true || r.status === 'active') || selectedRecipe;
  const licenseState = license?.active ? 'green' : 'amber';

  function handleRecipesChange(saved, action) {
    if (action === 'delete') {
      const deletedId = saved?.recipe_id || saved?.recipe?.recipe_id;
      const fallbackId = saved?.activated_fallback;
      setRecipes((prev) =>
        prev
          .filter((item) => item.recipe_id !== deletedId)
          .map((item) =>
            item.recipe_id === fallbackId ? { ...item, active: true, status: 'active' } : item
          )
      );
      setSelectedRecipeId((prev) => {
        if (fallbackId) return fallbackId;
        if (prev && prev !== deletedId) return prev;
        return '';
      });
    } else {
      setRecipes((prev) => {
        const rest = prev.filter((item) => item.recipe_id !== saved.recipe_id);
        const merged = saved.active ? rest.map((item) => ({ ...item, active: false, status: 'inactive' })) : rest;
        return [saved, ...merged].sort((a, b) => String(a.recipe_id).localeCompare(String(b.recipe_id)));
      });
      if (saved?.recipe_id) setSelectedRecipeId(saved.recipe_id);
    }
    fetchRecipes()
      .then((data) => {
        if (Array.isArray(data?.items)) setRecipes(data.items);
      })
      .catch(() => {});
  }

  const selectionValid = selected.length >= MIN_CAMERAS && selected.length <= maxCameras;
  const handleLicenseChange = useCallback((next) => {
    if (next) setLicense((prev) => ({ ...(prev || {}), ...next }));
  }, []);

  function toggleCamera(cameraId) {
    setSaveState(null);
    setSelected((prev) => {
      if (prev.includes(cameraId)) {
        if (prev.length <= MIN_CAMERAS) return prev;
        return prev.filter((id) => id !== cameraId);
      }
      if (prev.length >= maxCameras) return prev;
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

  const camerasPanel = (
      <article>
        <h3>{t('configuration.camerasTitle')}</h3>
        <p className="muted">
          {t('configuration.camerasHint', { min: MIN_CAMERAS, max: maxCameras })}
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
                (!checked && selected.length >= maxCameras) ||
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
                        {cam.available === false ? ` · ${t('configuration.camerasUnavailable')}` : ` · ${t('configuration.camerasOnline')}`})
                      </span>
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        )}
        <p className="muted">
          {t('configuration.camerasSelected')}: {selected.length}/{maxCameras}
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
  );

  const sectionPanels = {
    recipes: (
      <RecipeManager
        recipes={recipes}
        selectedRecipeId={selectedRecipe?.recipe_id || selectedRecipeId}
        onSelect={setSelectedRecipeId}
        onRecipesChange={handleRecipesChange}
        canWrite={canWriteRecipes}
        openHelp={openHelp}
      />
    ),
    thresholds: (
      <DecisionThresholds
        recipe={selectedRecipe}
        canWrite={canWriteRecipes}
        openHelp={openHelp}
        onRecipeChange={(saved) => handleRecipesChange(saved, 'update')}
      />
    ),
    cameras: camerasPanel,
    vision: <StationVisionSetup canConfigure={canConfigure} openHelp={openHelp} />,
    storage: <StorageEndurancePanel canConfigure={canConfigure} />,
    license: (
      <LicenseBilling
        license={license}
        canManage={canManageLicense}
        onLicenseChange={handleLicenseChange}
      />
    ),
  };

  function openSettingsItem(item) {
    if (item.screen && goTo) {
      goTo(item.screen);
      return;
    }
    setSettingsSection(item.id);
  }

  return (
    <section className="page-grid settings-page">
      <header className="page-intro">
        {settingsSection ? (
          <button type="button" className="text-btn" data-testid="settings-back" onClick={() => setSettingsSection('')}>
            {t('settings.back')}
          </button>
        ) : null}
        <p className="eyebrow">{t('settings.title')}</p>
        <h2>{settingsSection ? t(`settings.${settingsSection}`) : t('settings.title')}</h2>
        <p className="muted">{settingsSection ? t(`settings.${settingsSection}Hint`) : t('settings.hint')}</p>
        <ContextHelp articleId="configuration-overview" onOpen={openHelp} />
      </header>

      {!settingsSection ? (
        <>
          <div className="settings-status">
            <span className="muted">{t('common.recipe')}</span>
            <strong>{activeRecipe?.name || activeRecipe?.recipe_id || '—'}</strong>
            <span className="muted">{t('configuration.licenseTier')}</span>
            <StatusBadge state={licenseState}>{license?.active ? t('license.licensed') : t('license.unlicensed')}</StatusBadge>
          </div>
          <nav className="settings-list" aria-label={t('settings.title')}>
            {SETTINGS_ITEMS.map((item) => (
              <button
                key={item.id}
                type="button"
                className="settings-row"
                data-testid={item.testId}
                onClick={() => openSettingsItem(item)}
              >
                <span>
                  <strong>{t(item.labelKey)}</strong>
                  <span className="muted">{t(item.hintKey)}</span>
                </span>
                <span className="settings-chevron" aria-hidden="true">›</span>
              </button>
            ))}
          </nav>
        </>
      ) : (
        sectionPanels[settingsSection] || null
      )}
    </section>
  );
}

import { useEffect, useState } from 'react';
import { configSummary } from '../data/sampleData';
import StatusBadge from '../components/StatusBadge';
import ContextHelp from '../components/ContextHelp';
import { fetchLicenseStatus, fetchModels, fetchRecipes } from '../services';
import { useI18n } from '../i18n/I18nProvider';

export default function ConfigurationPage({ openHelp }) {
  const { t } = useI18n();
  const [license, setLicense] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [models, setModels] = useState([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [lic, recipeData, modelData] = await Promise.all([
          fetchLicenseStatus(),
          fetchRecipes().catch(() => ({ items: [] })),
          fetchModels().catch(() => ({ items: [] })),
        ]);
        if (!cancelled) {
          setLicense(lic);
          setRecipes(recipeData.items || []);
          setModels(modelData.items || []);
        }
      } catch {
        if (!cancelled) setLicense(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const licenseState = license?.active ? 'green' : 'amber';
  const activeRecipe = recipes.find((r) => r.status === 'active') || recipes[0];
  const activeModel = models.find((m) => m.status === 'active') || models[0];

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
    </section>
  );
}

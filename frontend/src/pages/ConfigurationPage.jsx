import { useEffect, useState } from 'react';
import { configSummary } from '../data/sampleData';
import StatusBadge from '../components/StatusBadge';
import { fetchLicenseStatus, fetchModels, fetchRecipes } from '../services';

export default function ConfigurationPage() {
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
          <p className="eyebrow">Configuration</p>
          <h2>Recipe & integration profile</h2>
          <p className="muted">Runtime config visibility (read-only in MVP).</p>
        </div>
        <StatusBadge state="green">Config valid</StatusBadge>
      </article>
      <article className="card kpi-grid">
        <div><label>OPC UA profile</label><strong>{configSummary.opcUaProfile}</strong></div>
        <div><label>Recipe version</label><strong>{activeRecipe?.recipe_version || configSummary.recipeVersion}</strong></div>
        <div><label>Model profile</label><strong>{activeModel?.name || configSummary.modelProfile}</strong></div>
        <div><label>Audit mode</label><strong>{configSummary.auditMode}</strong></div>
      </article>
      <article className="card kpi-grid">
        <div><label>License tier</label><strong>{license?.tier || 'n/a'}</strong></div>
        <div><label>License active</label><strong>{license ? String(license.active) : 'unknown'}</strong></div>
        <div><label>Grace active</label><strong>{license ? String(license.grace_active) : 'unknown'}</strong></div>
        <div><label>Status</label><StatusBadge state={licenseState}>{license?.active ? 'licensed' : 'unlicensed'}</StatusBadge></div>
      </article>
    </section>
  );
}

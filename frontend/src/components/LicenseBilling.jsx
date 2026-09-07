import { useEffect, useMemo, useState } from 'react';
import {
  cancelLicenseSubscription,
  fetchLicenseBilling,
  fetchLicenseCheckoutResult,
  fetchLicensePlans,
  openLicensePortal,
  startLicenseCheckout,
} from '../services';
import { useI18n } from '../i18n/I18nProvider';
import StatusBadge from './StatusBadge';

const EMAIL_KEY = 'amx_checkout_email';
const CHECKOUT_POLL_MS = 2000;
const CHECKOUT_POLL_ATTEMPTS = 5;

function readCheckoutParams() {
  if (typeof window === 'undefined') return { sessionId: '', state: '' };
  const params = new URLSearchParams(window.location.search);
  return {
    sessionId: params.get('session_id') || '',
    state: params.get('checkout') || '',
  };
}

function clearCheckoutParams() {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  if (!url.searchParams.has('session_id') && !url.searchParams.has('checkout')) return;
  url.searchParams.delete('session_id');
  url.searchParams.delete('checkout');
  window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
}

function currentPageUrls() {
  const origin = window.location.origin;
  const path = window.location.pathname || '/';
  return {
    successUrl: `${origin}${path}?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
    cancelUrl: `${origin}${path}?checkout=cancel`,
    returnUrl: `${origin}${path}?checkout=portal`,
  };
}

export default function LicenseBilling({ license, canManage, onLicenseChange }) {
  const { t } = useI18n();
  const [plans, setPlans] = useState([]);
  const [billing, setBilling] = useState(null);
  const [email, setEmail] = useState(() => {
    try {
      return sessionStorage.getItem(EMAIL_KEY) || '';
    } catch {
      return '';
    }
  });
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);
  const [plansError, setPlansError] = useState(null);

  const billingEnabled = Boolean(license?.billing_enabled);
  const features = useMemo(
    () => (Array.isArray(license?.features) ? license.features : []),
    [license]
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!billingEnabled) return;
      try {
        const data = await fetchLicensePlans();
        if (cancelled) return;
        const items = data.items || [];
        setPlans(items);
        setSelectedPlanId((prev) => prev || (items[0] ? String(items[0].id) : ''));
        setPlansError(null);
      } catch (err) {
        if (!cancelled) setPlansError(err.message || t('billing.plansFailed'));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [billingEnabled, t]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!billingEnabled) return;
      try {
        const data = await fetchLicenseBilling(email || undefined);
        if (!cancelled) setBilling(data);
      } catch {
        if (!cancelled) setBilling(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [billingEnabled, email, license?.active, license?.valid_until]);

  useEffect(() => {
    const { sessionId, state } = readCheckoutParams();
    if (state === 'cancel') {
      setNotice({ ok: false, message: t('billing.checkoutCancelled') });
      clearCheckoutParams();
      return;
    }
    if (state === 'portal') {
      setNotice({ ok: true, message: t('billing.portalReturned') });
      clearCheckoutParams();
      return;
    }
    if (!sessionId || !canManage) return;

    let cancelled = false;
    (async () => {
      setBusy('checkout');
      setNotice({ ok: true, message: t('billing.checkoutCompleting') });
      const storedEmail = email || (() => {
        try {
          return sessionStorage.getItem(EMAIL_KEY) || '';
        } catch {
          return '';
        }
      })();
      try {
        let result = null;
        for (let attempt = 0; attempt < CHECKOUT_POLL_ATTEMPTS; attempt += 1) {
          result = await fetchLicenseCheckoutResult(sessionId, storedEmail || undefined);
          if (result?.activated || result?.readyToActivate || result?.status === 'failed') break;
          await new Promise((resolve) => setTimeout(resolve, CHECKOUT_POLL_MS));
        }
        if (cancelled) return;
        if (result?.activated) {
          onLicenseChange?.(result.license || null);
          setNotice({ ok: true, message: t('billing.activated') });
        } else if (result?.status === 'failed') {
          setNotice({ ok: false, message: t('billing.checkoutFailed') });
        } else {
          setNotice({ ok: false, message: t('billing.checkoutPending') });
        }
      } catch (err) {
        if (!cancelled) setNotice({ ok: false, message: err.message || t('billing.checkoutFailed') });
      } finally {
        if (!cancelled) {
          setBusy('');
          clearCheckoutParams();
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [canManage, email, onLicenseChange, t]);

  function persistEmail(next) {
    setEmail(next);
    try {
      if (next) sessionStorage.setItem(EMAIL_KEY, next);
      else sessionStorage.removeItem(EMAIL_KEY);
    } catch {
      // ignore
    }
  }

  async function handleCheckout() {
    if (!canManage || !selectedPlanId) return;
    setBusy('checkout');
    setNotice(null);
    persistEmail(email);
    try {
      const urls = currentPageUrls();
      const result = await startLicenseCheckout({
        billingPlanId: Number(selectedPlanId),
        customerEmail: email,
        successUrl: urls.successUrl,
        cancelUrl: urls.cancelUrl,
      });
      if (!result?.url) throw new Error(t('billing.checkoutFailed'));
      window.location.assign(result.url);
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('billing.checkoutFailed') });
      setBusy('');
    }
  }

  async function handlePortal() {
    if (!canManage) return;
    setBusy('portal');
    setNotice(null);
    try {
      const result = await openLicensePortal({
        customerEmail: email || undefined,
        returnUrl: currentPageUrls().returnUrl,
      });
      if (!result?.url) throw new Error(t('billing.portalFailed'));
      window.location.assign(result.url);
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('billing.portalFailed') });
      setBusy('');
    }
  }

  async function handleCancel() {
    if (!canManage) return;
    if (!window.confirm(t('billing.cancelConfirm'))) return;
    setBusy('cancel');
    setNotice(null);
    try {
      const result = await cancelLicenseSubscription({
        customerEmail: email || undefined,
        cancelAtPeriodEnd: true,
      });
      if (result?.license) onLicenseChange?.(result.license);
      setBilling((prev) => ({
        ...(prev || {}),
        cancelAtPeriodEnd: true,
        subscriptionStatus: result?.status || prev?.subscriptionStatus,
        expiresAt: result?.expiresAt || prev?.expiresAt,
      }));
      setNotice({ ok: true, message: t('billing.cancelled') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('billing.cancelFailed') });
    } finally {
      setBusy('');
    }
  }

  const selectedPlan = plans.find((plan) => String(plan.id) === String(selectedPlanId));
  const licenseState = license?.active ? 'green' : 'amber';

  return (
    <article className="card" data-testid="license-billing">
      <h3>{t('billing.title')}</h3>
      <p className="muted">{t('billing.hint')}</p>

      <div className="kpi-grid billing-status">
        <div>
          <label>{t('configuration.licenseTier')}</label>
          <strong>{license?.tier || t('license.na')}</strong>
        </div>
        <div>
          <label>{t('configuration.status')}</label>
          <StatusBadge state={licenseState}>
            {license?.active ? t('license.licensed') : t('license.unlicensed')}
          </StatusBadge>
        </div>
        <div>
          <label>{t('billing.mode')}</label>
          <strong>{license?.mode || t('license.na')}</strong>
        </div>
        <div>
          <label>{t('billing.validUntil')}</label>
          <strong>{license?.valid_until || billing?.expiresAt || t('license.na')}</strong>
        </div>
      </div>

      {features.length ? (
        <p className="muted" data-testid="license-features">
          {t('billing.features')}: {features.join(', ')}
        </p>
      ) : null}

      {billing?.available ? (
        <div className="kpi-grid">
          <div>
            <label>{t('billing.subscription')}</label>
            <strong>{billing.subscriptionStatus || (billing.hasStripeSubscription ? t('billing.active') : t('billing.none'))}</strong>
          </div>
          <div>
            <label>{t('billing.cancelAtPeriodEnd')}</label>
            <strong>{billing.cancelAtPeriodEnd ? t('common.yes') : t('common.no')}</strong>
          </div>
        </div>
      ) : null}

      {!billingEnabled ? (
        <p className="muted">{t('billing.serverNotConfigured')}</p>
      ) : (
        <>
          {plansError ? <p className="error" role="status">{plansError}</p> : null}
          {plans.length ? (
            <ul className="plan-list">
              {plans.map((plan) => (
                <li key={plan.id}>
                  <label className="plan-card">
                    <input
                      type="radio"
                      name="billing-plan"
                      value={plan.id}
                      checked={String(selectedPlanId) === String(plan.id)}
                      disabled={!canManage || Boolean(busy)}
                      onChange={() => setSelectedPlanId(String(plan.id))}
                    />
                    <span>
                      <strong>{plan.name}</strong>
                      <span className="muted">
                        {' '}
                        · {plan.billingModel}
                        {plan.productName ? ` · ${plan.productName}` : ''}
                        {Array.isArray(plan.features) && plan.features.length
                          ? ` · ${plan.features.join(', ')}`
                          : ''}
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">{t('billing.noPlans')}</p>
          )}

          {canManage ? (
            <div className="billing-form">
              <label>
                {t('billing.email')}
                <input
                  type="email"
                  autoComplete="email"
                  value={email}
                  disabled={Boolean(busy)}
                  onChange={(event) => persistEmail(event.target.value)}
                  placeholder={license?.customer_email_masked || 'billing@example.com'}
                />
              </label>
              <div className="billing-actions">
                <button
                  type="button"
                  className="tab active"
                  data-testid="license-checkout"
                  disabled={!selectedPlan || Boolean(busy) || !email}
                  onClick={handleCheckout}
                >
                  {busy === 'checkout' ? t('billing.startingCheckout') : t('billing.buy')}
                </button>
                <button
                  type="button"
                  className="tab"
                  data-testid="license-portal"
                  disabled={Boolean(busy) || !(billing?.canOpenPortal || license?.license_key_masked)}
                  onClick={handlePortal}
                >
                  {busy === 'portal' ? t('billing.openingPortal') : t('billing.portal')}
                </button>
                <button
                  type="button"
                  className="tab"
                  data-testid="license-cancel"
                  disabled={Boolean(busy) || !billing?.canCancel}
                  onClick={handleCancel}
                >
                  {busy === 'cancel' ? t('billing.cancelling') : t('billing.cancel')}
                </button>
              </div>
            </div>
          ) : (
            <p className="muted">{t('billing.readOnly')}</p>
          )}
        </>
      )}

      {notice ? (
        <p className={notice.ok ? 'ok' : 'error'} role="status">
          {notice.message}
        </p>
      ) : null}
    </article>
  );
}

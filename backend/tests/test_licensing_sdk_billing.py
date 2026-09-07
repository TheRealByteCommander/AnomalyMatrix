"""SDK tRPC helpers and public Stripe billing procedures."""

import json

from app.licensing_sdk.client import LicenseClient, LicensingApiError
from app.licensing_sdk.trpc import unwrap_result, wrap_input


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.is_success = 200 <= status < 300

    def json(self):
        return self._payload


class _FakeClient:
    last = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, params=None):
        _FakeClient.last = {"method": "GET", "url": url, "params": params}
        if url.endswith("stripe.plans.listPublic"):
            return _FakeResponse({"result": {"data": {"json": []}}})
        if url.endswith("stripe.getCheckoutResult"):
            return _FakeResponse(
                {
                    "result": {
                        "data": {
                            "json": {
                                "status": "completed",
                                "readyToActivate": True,
                                "sessionId": "cs_test",
                                "licenseKey": "AMX-LIVE-KEY-9999",
                            }
                        }
                    }
                }
            )
        if url.endswith("stripe.getLicenseBilling"):
            return _FakeResponse(
                {
                    "result": {
                        "data": {
                            "json": {
                                "licenseKey": "AMX-LIVE-KEY-9999",
                                "canCancel": True,
                                "canOpenPortal": True,
                            }
                        }
                    }
                }
            )
        return _FakeResponse({"result": {"data": {"json": {}}}})

    def post(self, url, json=None):
        _FakeClient.last = {"method": "POST", "url": url, "json": json}
        if url.endswith("stripe.createCheckoutSession"):
            return _FakeResponse(
                {
                    "result": {
                        "data": {
                            "json": {
                                "sessionId": "cs_test",
                                "url": "https://checkout.stripe.com/c/pay/cs_test",
                                "billingModel": "subscription",
                            }
                        }
                    }
                }
            )
        if url.endswith("stripe.createCustomerPortalSession"):
            return _FakeResponse({"result": {"data": {"json": {"url": "https://billing.stripe.com/p/session"}}}})
        if url.endswith("stripe.cancelSubscription"):
            return _FakeResponse(
                {
                    "result": {
                        "data": {
                            "json": {
                                "success": True,
                                "cancelAtPeriodEnd": True,
                                "status": "active",
                                "expiresAt": "2026-12-01T00:00:00Z",
                            }
                        }
                    }
                }
            )
        return _FakeResponse({"error": {"json": {"message": "nope", "data": {"code": "NOT_FOUND"}}}}, status=404)


def test_unwrap_result_keeps_empty_list():
    assert unwrap_result({"result": {"data": {"json": []}}}) == []
    assert wrap_input(None) == {"json": {}}


def test_sdk_billing_hooks(monkeypatch):
    monkeypatch.setattr("app.licensing_sdk.client.httpx.Client", _FakeClient)
    client = LicenseClient(server_url="https://licadmin.example", product_id=2)

    assert client.list_public_plans() == []
    assert "stripe.plans.listPublic" in _FakeClient.last["url"]
    assert _FakeClient.last["method"] == "GET"
    assert json.loads(_FakeClient.last["params"]["input"]) == {"json": {}}

    checkout = client.create_checkout_session(
        billing_plan_id=9,
        customer_email="ops@example.com",
        success_url="http://127.0.0.1:5173/?checkout=success&session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://127.0.0.1:5173/?checkout=cancel",
    )
    assert checkout["sessionId"] == "cs_test"
    assert _FakeClient.last["json"]["json"]["billingPlanId"] == 9

    result = client.get_checkout_result("cs_test", email="ops@example.com")
    assert result["readyToActivate"] is True
    assert result["licenseKey"] == "AMX-LIVE-KEY-9999"

    billing = client.get_license_billing(license_key="AMX-LIVE-KEY-9999", customer_email="ops@example.com")
    assert billing["canCancel"] is True

    portal = client.create_customer_portal_session(
        license_key="AMX-LIVE-KEY-9999",
        customer_email="ops@example.com",
        return_url="http://127.0.0.1:5173/",
    )
    assert portal["url"].startswith("https://billing.stripe.com")

    cancel = client.cancel_subscription(
        license_key="AMX-LIVE-KEY-9999",
        customer_email="ops@example.com",
    )
    assert cancel["success"] is True
    assert cancel["cancelAtPeriodEnd"] is True


def test_sdk_maps_trpc_error(monkeypatch):
    monkeypatch.setattr("app.licensing_sdk.client.httpx.Client", _FakeClient)
    client = LicenseClient(server_url="https://licadmin.example", product_id=2)
    try:
        client._post("stripe.unknown", {})
        raise AssertionError("expected LicensingApiError")
    except LicensingApiError as exc:
        assert exc.code == "NOT_FOUND"

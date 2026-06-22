from datetime import datetime, timedelta, timezone

from app.licensing import LicenseManager, _offline_grace_hours


def test_license_validate_interval_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv('LICENSE_STATE_FILE', str(tmp_path / 'license_state.json'))
    monkeypatch.setenv('LICENSE_VALIDATE_INTERVAL_SEC', '120')
    m = LicenseManager()
    assert m.validation_interval_sec == 120


def test_license_enforce_blocks_without_activation(tmp_path, monkeypatch):
    monkeypatch.setenv('LICENSE_STATE_FILE', str(tmp_path / 'license_state.json'))
    monkeypatch.setenv('LICENSE_ENFORCE', 'true')
    m = LicenseManager()
    try:
        m.enforce_feature('inspection.run')
        raise AssertionError('expected PermissionError')
    except PermissionError:
        pass


def test_offline_grace_hours_env(monkeypatch):
    monkeypatch.setenv('LICENSE_OFFLINE_GRACE_HOURS', '48')
    assert _offline_grace_hours() == 48

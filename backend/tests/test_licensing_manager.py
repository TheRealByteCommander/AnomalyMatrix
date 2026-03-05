from datetime import datetime, timedelta, timezone

from app.licensing import LicenseManager


def test_validate_once_offline_grace(tmp_path, monkeypatch):
    monkeypatch.setenv('LICENSE_STATE_FILE', str(tmp_path / 'license_state.json'))
    monkeypatch.delenv('LICENSE_SERVER_URL', raising=False)
    m = LicenseManager()
    m._save({
        'active': True,
        'tier': 'basic',
        'features': ['inspection.run', 'inspection.read'],
        'token': 't',
        'license_key': 'k',
        'valid_until': None,
        'last_validation_at': None,
        'offline_grace_until': (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        'last_error': None,
    })
    st = m.validate_once()
    assert st['active'] is True


def test_enforce_feature_negative(tmp_path, monkeypatch):
    monkeypatch.setenv('LICENSE_STATE_FILE', str(tmp_path / 'license_state.json'))
    m = LicenseManager()
    m._save({
        'active': True,
        'tier': 'basic',
        'features': ['inspection.read'],
        'token': 't',
        'license_key': 'k',
        'valid_until': None,
        'last_validation_at': None,
        'offline_grace_until': None,
        'last_error': None,
    })
    try:
        m.enforce_feature('inspection.run')
        raise AssertionError('expected PermissionError')
    except PermissionError:
        pass

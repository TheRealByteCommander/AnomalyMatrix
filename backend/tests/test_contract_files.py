from pathlib import Path
import json


def test_contract_files_present_and_parseable():
    root = Path(__file__).resolve().parents[2]
    files = [
        root / 'contracts' / 'api_envelope_v1.json',
        root / 'contracts' / 'opcua_nodeset_mapping_v1.json',
        root / 'contracts' / 'events_v1' / 'InspectionCompleted.json',
        root / 'contracts' / 'events_v1' / 'FeedbackSubmitted.json',
        root / 'contracts' / 'events_v1' / 'ModelRetrained.json',
        root / 'contracts' / 'events_v1' / 'TrendWarningRaised.json',
    ]
    for file in files:
        assert file.exists(), f"missing contract: {file}"
        payload = json.loads(file.read_text(encoding='utf-8'))
        assert payload

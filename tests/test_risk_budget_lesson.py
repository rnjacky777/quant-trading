import json

import pytest

from app.backtest import lessons


@pytest.mark.parametrize('corruption', [None, 'duplicate', 'fingerprint', 'incomplete'])
def test_risk_budget_evidence_audit(tmp_path, monkeypatch, corruption):
    monkeypatch.setattr(lessons, 'LESSONS', ())
    rows = [dict(variant=v, year=y, fee_bps=f, slippage_bps=s,
                 input_fingerprints={'candles': 'same'}, result={'metrics': {'total_return': 0.01}})
            for v in ('parent', 'child') for y in range(2022, 2026)
            for f, s in ((5, 5), (10, 5), (10, 10), (20, 10))]
    data = dict(status='completed', rows=rows, parent='parent', candidate='child',
                decision='reject_objective_a_solution', objectives={})
    if corruption == 'duplicate':
        rows[-1] = rows[-2]
    elif corruption == 'fingerprint':
        rows[-1]['input_fingerprints'] = {'candles': 'different'}
    elif corruption == 'incomplete':
        data['status'] = 'failed'
    (tmp_path / 'perpetual-risk-budget-055.json').write_text(json.dumps(data), encoding='utf-8')
    if corruption:
        with pytest.raises(ValueError):
            lessons.research_lessons(tmp_path)
    else:
        result = lessons.research_lessons(tmp_path)
        assert len(result['lessons'][0]['comparisons']) == 16
        assert result['lessons'][0]['independent_validation'] is False

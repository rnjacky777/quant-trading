import pytest

from app.backtest.signal_diagnostics import horizon_outcome, summarize_signals
from app.data.models import Candle, FundingRate


def candle(hour,price=100):
    return Candle("test","BTC/USDT","1h",hour*3600000,price,price,price,price,1)


@pytest.mark.parametrize("side",[1,-1])
def test_fixed_horizon_fill_cost_accounting_and_funding_boundaries(side):
    funding=[FundingRate("test","BTC/USDT",3600000,.9,100),
             FundingRate("test","BTC/USDT",3600001,.01,100),
             FundingRate("test","BTC/USDT",18000000,.02,100),
             FundingRate("test","BTC/USDT",18000001,.9,100)]
    result=horizon_outcome(candle(1),candle(5),side,fee_bps=0,slippage_bps=0,funding=funding)
    assert result['funding_return']==pytest.approx(-side*.03)
    assert result['net_return']==result['funding_return']
    costed=horizon_outcome(candle(1),candle(5,110),side,fee_bps=10,slippage_bps=5,funding=[])
    entry=100*(1+side*.0005);exit=110*(1-side*.0005)
    expected=(side*(exit-entry)-.001*(entry+exit))/entry
    assert costed['net_return']==pytest.approx(expected)
    assert costed['slippage_fraction']>0 and costed['fee_fraction']>0


def test_censored_observations_are_counted_and_overlap_sensitivity_is_distinct():
    events=[]
    for hour,value in ((0,.1),(1,-.1),(2,None)):
        obs=dict(status='observed',net_return=value,gross_return=value,reference_price_return=value,
                 slippage_fraction=0,fee_fraction=0,funding_return=0) if value is not None else dict(status='censored')
        events.append(dict(timestamp_ms=hour*3600000,sleeve='intraday',direction=1,
            outcome=dict(status='accepted',reason='full_budget'),horizons={str(h):dict(obs) for h in (4,12,24)}))
    row=next(r for r in summarize_signals(events) if r['scope']=='all' and r['hours']==4)
    assert row['signal_count']==3 and row['observed_count']==2 and row['censored_count']==1
    assert row['mean_net_return']==0 and row['positive_fraction']==.5
    assert row['nonoverlap_count']==1 and row['nonoverlap_mean_net']==.1
    assert row['unique_entry_days']==1
    result=horizon_outcome(candle(1),None,1,fee_bps=10,slippage_bps=5,funding=[])
    assert result['status']=='censored' and 'net_return' not in result

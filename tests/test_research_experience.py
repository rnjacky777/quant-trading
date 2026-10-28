from datetime import datetime, timezone
import json

import pytest

from app.backtest import lessons
from app.backtest.path_diagnostics import completed_close_path, monthly_equity
from app.data.models import Candle


def test_lessons_require_all_cost_periods_and_matching_fingerprints(tmp_path,monkeypatch):
    monkeypatch.setattr(lessons,"LESSONS",(("one","parent.json","p","child.json","c","hypothesis","one change","not adopted","scope limited"),))
    rows=[dict(year=y,cost_multiplier=c,variant="p",status="completed",input_fingerprints={"data":"fixed"},
               result=dict(metrics=dict(total_return=.01,maximum_drawdown=-.02)))
          for y in (2024,2025) for c in (1,2)]
    (tmp_path/"parent.json").write_text(json.dumps(dict(rows=rows)))
    child=[dict(r,variant="c") for r in rows]
    target=tmp_path/"child.json"
    target.write_text(json.dumps(dict(rows=child)))
    result=lessons.research_lessons(tmp_path)
    assert len(result['lessons'][0]['comparisons'])==4
    assert not result['lessons'][0]['independent_validation']
    target.write_text(json.dumps(dict(rows=child[:-1])))
    with pytest.raises(ValueError,match="four unique"):
        lessons.research_lessons(tmp_path)
    child[0]['input_fingerprints']={"data":"changed"}
    target.write_text(json.dumps(dict(rows=child)))
    with pytest.raises(ValueError,match="mismatched"):
        lessons.research_lessons(tmp_path)


def test_monthly_equity_includes_floating_changes_not_only_trade_settlements():
    stamps=[int(datetime(2025,m,1,tzinfo=timezone.utc).timestamp()*1000) for m in range(1,13)]
    result=dict(initial_cash=1000,equity_curve=[dict(timestamp_ms=t,equity=1000+10*i) for i,t in enumerate(stamps)],
                trades=[dict(exit_timestamp_ms=stamps[1],pnl=3)])
    months=monthly_equity(result,2025)
    assert months[1]['equity_change']==10 and months[1]['closed_trade_pnl']==3
    assert months[1]['return_fraction']==pytest.approx(.01)
    assert sum(m['equity_change'] for m in months)==110
    result['equity_curve']=result['equity_curve'][:-1]
    with pytest.raises(ValueError,match="twelve"):
        monthly_equity(result,2025)


@pytest.mark.parametrize("side",[1,-1])
def test_completed_close_path_excludes_exit_bar_and_handles_direction(side):
    trade=dict(entry_timestamp_ms=3600000,exit_timestamp_ms=7200000,
               entry_price=100,stop_loss_price=100-side*10,direction=side,pnl=-5)
    prices=[100+side*10,100-side*50]
    bars=[Candle("test","BTC/USDT","1h",(i+1)*3600000,p,p,p,p,1) for i,p in enumerate(prices)]
    path=completed_close_path(trade,bars)
    assert path['completed_hours']==1
    assert path['max_favorable_close_r']==1 and path['max_adverse_close_r']==0
    assert path['lost_after_1r_close']
    trade['exit_timestamp_ms']=trade['entry_timestamp_ms']
    assert completed_close_path(trade,bars)['completed_hours']==0

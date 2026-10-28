from dataclasses import asdict, fields
import json

from fastapi.testclient import TestClient

from app.api.main import app
from app.backtest.directional_evidence import load_directional_evidence
from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.models import PerformanceMetrics
from app.portfolio.research_risk import PortfolioLimits


def snapshot():
    metrics={f.name:0 for f in fields(PerformanceMetrics)}
    metrics.update(total_return=.001,number_of_trades=1,net_funding=.1)
    return dict(year=2024,mode="both",cost_multiplier=1,status="completed",
        config=asdict(PerpetualResearchConfig()),input_fingerprints={},result=dict(
            metrics=metrics,final_equity=10010,equity_curve=[dict(equity=10000,timestamp_ms=1704067200000),
                dict(equity=10010,timestamp_ms=1704070800000)],trades=[dict(direction=-1,
                entry_timestamp_ms=1704067200000,exit_timestamp_ms=1704070800000,
                entry_price=100,exit_price=90,entry_notional=100,leverage=1,pnl=10,funding=.1,exit_reason="signal")]))


def test_directional_catalog_lists_filters_and_renders_short_curve(tmp_path,monkeypatch):
    monkeypatch.setenv("QUANT_DB_PATH",str(tmp_path/"market.sqlite3"))
    base=snapshot()
    (tmp_path/"perpetual-direction-research.json").write_text(json.dumps(dict(rows=[base])),encoding="utf-8")
    child=dict(base,variant="asia_session")
    (tmp_path/"perpetual-entry-filters.json").write_text(json.dumps(dict(rows=[child])),encoding="utf-8")
    entries=load_directional_evidence(tmp_path)
    assert len({e['id'] for e in entries})==2
    client=TestClient(app)
    response=client.get("/derivatives-research")
    assert response.status_code==200 and len(response.context['entries'])==2
    response=client.get("/derivatives-research",params=dict(experiment=entries[0]['id']))
    assert response.status_code==200
    assert "做空" in response.text and "合約多空資產曲線" in response.text
    assert '<polyline class="chart-line"' in response.text
    assert client.get("/derivatives-research",params=dict(year=2025)).context['entries']==[]
    assert client.get("/derivatives-research",params=dict(cost=2)).context['entries']==[]
    assert client.get("/derivatives-research",params=dict(experiment="f"*64)).status_code==404
    portfolio=json.loads(json.dumps(base))
    portfolio.update(variant="portfolio_combined",portfolio_limits=asdict(PortfolioLimits(same_direction_risk_decay=True)),
        summary=dict(maximum_concurrent_positions=2))
    portfolio['result']['trades'][0].update(sleeve="swing",position_id="swing:1704067200000:1")
    portfolio['result']['portfolio_curve']=[dict(open_positions=2),dict(open_positions=0)]
    (tmp_path/"perpetual-portfolio-research.json").write_text(json.dumps(dict(rows=[portfolio])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['label']=="短線＋波段共用資金")
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "波段 #1" in response.text and "最多同時持有" in response.text
    assert "多部位持倉數時間軸" in response.text
    assert "同向加倉風控" in response.text
    assert "全年進場頻率（UTC）" in response.text and "全年合計" in response.text
    assert response.context['selected']['frequency']['total']==1
    assert response.context['selected']['frequency']['intraday']==0
    assert response.context['chart_points']=="0.0,260.0 900.0,0.0"
    protected=json.loads(json.dumps(portfolio))
    protected.update(variant="portfolio_swing_protection",swing_price_protection=dict(activation_r=1))
    protected['result']['trades'][0]['exit_reason']='profit_protection'
    (tmp_path/"perpetual-swing-protection.json").write_text(json.dumps(dict(rows=[protected])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_swing_protection')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200
    assert "價格保本不等於扣費後保本" in response.text and "價格保護止損" in response.text
    guarded=json.loads(json.dumps(portfolio))
    guarded['variant']='portfolio_sweep_mean_guard'
    (tmp_path/"perpetual-sweep-mean-guard.json").write_text(json.dumps(dict(rows=[guarded])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_sweep_mean_guard')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "短線空單位置限制" in response.text
    assert "沒有穩定提升收益" in response.text
    structural=json.loads(json.dumps(portfolio))
    structural.update(variant="portfolio_sweep_structural_stop",intraday_exit_rule="perpetual_sweep_initial_stop_at_sweep_extreme")
    structural['result']['trades'][0]['stop_loss_price']=105
    (tmp_path/"perpetual-sweep-structural-stop.json").write_text(json.dumps(dict(rows=[structural])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_sweep_structural_stop')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "掃單結構止損" in response.text
    assert "初始止損" in response.text and "105.00" in response.text
    loss_guard=json.loads(json.dumps(structural))
    loss_guard.update(variant="portfolio_directional_loss_guard",directional_loss_guard=True)
    (tmp_path/"perpetual-directional-loss-guard.json").write_text(json.dumps(dict(rows=[loss_guard])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_directional_loss_guard')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "同方向連虧保護" in response.text
    assert "兩個減半不相乘" in response.text
    context_exit=json.loads(json.dumps(loss_guard))
    context_exit.update(variant="portfolio_sweep_context_exit",intraday_exit_rule="perpetual_sweep_structural_stop_4h_context_exit")
    (tmp_path/"perpetual-sweep-context-exit.json").write_text(json.dumps(dict(rows=[context_exit])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_sweep_context_exit')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "本候選短線不再因 1H 反向通道退出" in response.text
    assert "同方向連虧保護仍保留" in response.text
    confirmed=json.loads(json.dumps(loss_guard))
    confirmed['variant']='portfolio_sweep_structure_confirm'
    (tmp_path/"perpetual-sweep-structure-confirm.json").write_text(json.dumps(dict(rows=[confirmed])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_sweep_structure_confirm')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "三根微結構確認" in response.text
    assert "同方向連虧保護" in response.text and "掃單結構止損" in response.text
    failure=json.loads(json.dumps(confirmed))
    failure.update(variant='portfolio_swing_failure_exit',swing_failure_exit=True)
    failure['result']['trades'][0]['exit_reason']='breakout_failure'
    (tmp_path/"perpetual-swing-failure-exit.json").write_text(json.dumps(dict(rows=[failure])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_swing_failure_exit')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "波段突破失效退出" in response.text
    assert "三根微結構確認" in response.text and "同方向連虧保護" in response.text
    slope=json.loads(json.dumps(failure))
    slope.update(variant='portfolio_slope_risk_cap',slope_risk_cap=True)
    (tmp_path/"perpetual-slope-risk-cap.json").write_text(json.dumps(dict(rows=[slope])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_slope_risk_cap')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "斜率衝突風險上限" in response.text
    assert "三根微結構確認" in response.text and "波段突破失效退出" in response.text
    ablation=json.loads(json.dumps(failure))
    ablation['variant']='portfolio_sweep_no_atr_floor'
    (tmp_path/"perpetual-atr-ablation.json").write_text(json.dumps(dict(rows=[ablation])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_sweep_no_atr_floor')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "移除1H ATR門檻未採用" in response.text
    assert "三根微結構確認" in response.text and "波段突破失效退出" in response.text
    volume=json.loads(json.dumps(failure))
    volume['variant']='portfolio_swing_volume'
    (tmp_path/"perpetual-swing-volume.json").write_text(json.dumps(dict(rows=[volume])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_swing_volume')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "波段確認成交量門檻" in response.text
    assert "三根微結構確認" in response.text and "波段突破失效退出" in response.text
    intraday_protected=json.loads(json.dumps(failure))
    intraday_protected.update(variant='portfolio_intraday_protection',intraday_price_protection=dict(activation_r=1))
    (tmp_path/"perpetual-intraday-protection.json").write_text(json.dumps(dict(rows=[intraday_protected])),encoding="utf-8")
    entry=next(e for e in load_directional_evidence(tmp_path) if e['row'].get('variant')=='portfolio_intraday_protection')
    response=client.get("/derivatives-research",params=dict(experiment=entry['id']))
    assert response.status_code==200 and "短線1R價格保護未採用" in response.text
    assert "三根微結構確認" in response.text and "波段突破失效退出" in response.text


def test_missing_catalog_is_empty_and_corrupt_artifact_is_not_silently_omitted(tmp_path,monkeypatch):
    monkeypatch.setenv("QUANT_DB_PATH",str(tmp_path/"market.sqlite3"))
    client=TestClient(app)
    assert client.get("/derivatives-research").status_code==200
    (tmp_path/"perpetual-direction-research.json").write_text('{"rows":oops}',encoding="utf-8")
    response=client.get("/derivatives-research")
    assert response.status_code==503 and "研究快照格式錯誤" in response.text

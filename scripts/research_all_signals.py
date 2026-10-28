"""Replay frozen baseline and diagnose every qualified signal, not only fills."""
from bisect import bisect_left
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.long_short_research import PerpetualResearchConfig
from app.backtest.portfolio_research import PortfolioResearchEngine, ResearchSleeve
from app.backtest.results import serialize_result
from app.backtest.signal_diagnostics import HORIZONS, horizon_outcome, summarize_signals
from app.data.aggregation import completed_four_hour_bars
from app.data.models import Candle, FundingRate, MarkPriceCandle
from app.portfolio.research_risk import PortfolioLimits
from app.strategies.pa_smc import DirectionalSweepStrategy
from app.strategies.swing_efficiency import DirectionalSwingEfficiencyStrategy, path_efficiency
from scripts.research_perpetual_directions import fingerprint


def main() -> None:
    parent_path=Path("data/perpetual-confirmed-efficiency.json")
    root=Path("data/btc-perpetual-1h")
    tape=[Candle("binance-usdm","BTC/USDT","1h",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close','volume')]) for r in json.loads((root/"klines.json").read_text())]
    marks=[MarkPriceCandle("binance-usdm","BTC/USDT",int(r['open_time']),
        *[float(r[k]) for k in ('open','high','low','close')],timeframe="1h") for r in json.loads((root/"markPriceKlines.json").read_text())]
    funding=[FundingRate("binance-usdm","BTC/USDT",int(r['fundingTime']),float(r['fundingRate']),float(r['markPrice']))
             for r in json.loads((root/"funding-api.json").read_text())]
    parents=json.loads(parent_path.read_text())['rows']
    if len(parents)!=4 or {(r['year'],r['cost_multiplier']) for r in parents}!={(2024,1),(2024,2),(2025,1),(2025,2)}:
        raise ValueError("all four unique baseline cases required")
    cases=[];replays=[];identities={}
    for parent in parents:
        if parent['variant']!='portfolio_confirmed_efficiency' or parent['status']!='completed':
            raise ValueError("wrong or failed baseline evidence")
        year=parent['year'];start=1704067200000 if year==2024 else 1735689600000
        end=1735689600000 if year==2024 else 1767225600000
        period=[c for c in tape if start-243*3600000<=c.timestamp_ms<end]
        index={c.timestamp_ms:i for i,c in enumerate(period)}
        period_marks=[c for c in marks if start<=c.timestamp_ms<end]
        rates=[f for f in funding if start<=f.timestamp_ms<end]
        fingerprints=dict(candles=fingerprint([asdict(c) for c in period]),marks=fingerprint([asdict(m) for m in period_marks]),funding=fingerprint([asdict(f) for f in rates]))
        if fingerprints!=parent['input_fingerprints']:
            raise ValueError("baseline data fingerprints changed")
        strategies=dict(intraday=DirectionalSweepStrategy(),swing=DirectionalSwingEfficiencyStrategy())
        if any(s['strategy']!=strategies[s['name']].name for s in parent['sleeves']):
            raise ValueError("strategy identity differs from baseline")
        sleeves=[ResearchSleeve(s['name'],strategies[s['name']],PerpetualResearchConfig(**s['config'])) for s in parent['sleeves']]
        configs={s.name:s.config for s in sleeves}
        events=[]
        result=PortfolioResearchEngine(sleeves,PortfolioLimits(**parent['portfolio_limits'])).run(
            period,evaluation_start_ms=start,marks=period_marks,funding=rates,signal_observer=events.append)
        if json.loads(serialize_result(result))!=parent['result']:
            raise ValueError("instrumented replay changed baseline full snapshot")
        accepted=[e for e in events if e['outcome']['status']=='accepted']
        if len(accepted)!=len(result.trades) or {e['outcome']['position_id'] for e in accepted}!={t.position_id for t in result.trades}:
            raise ValueError("accepted signal/fill identity mismatch")
        event_keys={(e['timestamp_ms'],e['sleeve'],e['direction']) for e in events}
        if len(event_keys)!=len(events):
            raise ValueError("duplicate qualified signal identity")
        if year in identities and event_keys!=identities[year]:
            raise ValueError("costs unexpectedly changed raw signal set")
        identities[year]=event_keys
        for event in events:
            j=index[event['timestamp_ms']];history=period[:j];last=history[-1]
            bars=completed_four_hour_bars(history)
            atr=sum(max(history[k].high-history[k].low,abs(history[k].high-history[k-1].close),abs(history[k].low-history[k-1].close))
                    for k in range(len(history)-14,len(history)))/14
            event['entry_known_features']=dict(atr14_fraction=atr/last.close,
                four_hour_er20=path_efficiency([c.close for c in bars[-21:]]))
            event['execution_open_gap_fraction']=event['direction']*(period[j].open-last.close)/last.close
            config=configs[event['sleeve']]
            event['horizons']={}
            for hours in HORIZONS:
                target=event['timestamp_ms']+hours*3600000
                exit_bar=period[index[target]] if target<end and target in index else None
                event['horizons'][str(hours)]=horizon_outcome(period[j],exit_bar,event['direction'],
                    fee_bps=config.fee_bps,slippage_bps=config.slippage_bps,funding=rates)
        counts=Counter((e['outcome']['status'],e['outcome']['reason']) for e in events)
        case=dict(year=year,cost=parent['cost_multiplier'],strategy_variant=parent['variant'],
            actual_portfolio_metrics=parent['result']['metrics'],input_fingerprints=fingerprints,
            selection_counts=[dict(status=s,reason=r,count=n) for (s,r),n in sorted(counts.items())],
            summaries=summarize_signals(events),signals=events)
        cases.append(case)
        replays.append(dict(year=year,cost=parent['cost_multiplier'],full_snapshot_equal=True,
            raw_signal_count=len(events),accepted_count=len(accepted),signal_set_equal_across_costs=True))
        print(year,parent['cost_multiplier'],'signals',len(events),'selection',dict(counts),flush=True)
        for group in case['summaries']:
            if group['scope']=='all' and group['hours']==24:
                print(group['sleeve'],group['direction'],'N',group['observed_count'],'net24',round(group['mean_net_return']*100,3) if group['mean_net_return'] is not None else None,flush=True)
        Path("data/all-signal-diagnostics.json").write_text(json.dumps(dict(
            schema="fixed_horizon_signal_diagnostic_v1",used_for_tuning=True,independent_validation=False,
            is_executable_portfolio_return=False,warning="Fixed-horizon events ignore stops, liquidation, dynamic exits and shared budgets; overlapping samples are not independent. Never sum into annual returns.",cases=cases),allow_nan=False),encoding="utf-8")
    sources=[parent_path,root/"klines.json",root/"markPriceKlines.json",root/"funding-api.json",Path(__file__),
             Path("app/backtest/portfolio_research.py"),Path("app/backtest/signal_diagnostics.py"),
             Path("app/strategies/pa_smc.py"),Path("app/strategies/directional_intraday.py"),
             Path("app/strategies/directional_swing.py"),Path("app/strategies/swing_confirmation.py"),Path("app/strategies/swing_efficiency.py")]
    Path("data/all-signal-audit.json").write_text(json.dumps(dict(status="completed_diagnostic_only",
        sources={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},cases=replays,
        orders_submitted=False,new_strategy_version=None),indent=2),encoding="utf-8")
    write_report(cases)


def percentage(value: float | None) -> str:
    return "—" if value is None else f"{value:+.3%}"


def write_report(cases: list[dict]) -> None:
    lines=["# 完整訊號診斷：包含未成交機會", "", "2026-10-28。固定portfolio_confirmed_efficiency，10項研究經驗後不先調參。四筆原行情／mark／funding指紋一致；觀察器啟用時整份回測快照仍逐一與父完全相同，准入結果不是事後猜測。", "",
        "## 如何解讀", "", "全部合格訊號包含成交、被風控／每日名額拒絕、退出當根未再進場。4／12／24h從訊號完成後下一根開盤起，固定時間開盤退出，扣同父費用／滑價及該期間實際funding，以entry-fill名目本金正規化。它忽略原止損、動態退出、強平及共享資金，不是可執行策略收益，也不加總或複利成年度收益。", "",
        "Funding邊界為entry實際時間<事件≤exit實際時間。年底缺完整窗口的訊號保留censored，不用下一年補；正常／雙成本原訊號集合完全一致。重疊事件與成本案例非獨立樣本；nonoverlap敏感度只在每個同方向同策略分組按時間選間隔H的事件，跨組仍可相關，不宣稱統計顯著。", "",
        "## 原可執行組合績效（未變更）", "", "|年|成本倍數|淨收益|最大回撤|交易數|", "|---|---:|---:|---:|---:|"]
    for c in cases:
        m=c['actual_portfolio_metrics']
        lines.append(f"|{c['year']}|{c['cost']}|{m['total_return']:+.3%}|{m['maximum_drawdown']:.3%}|{m['number_of_trades']}|")
    lines += ["", "## 真實訊號准入分類", "", "|年|成本倍數|策略|方向|全部訊號|已成交|被拒絕|退出當根跳過|", "|---|---:|---|---|---:|---:|---:|---:|"]
    for c in cases:
        for sleeve in ('intraday','swing'):
            for side in (1,-1):
                es=[e for e in c['signals'] if e['sleeve']==sleeve and e['direction']==side]
                states=Counter(e['outcome']['status'] for e in es)
                lines.append(f"|{c['year']}|{c['cost']}|{'短線' if sleeve=='intraday' else '波段'}|{'多' if side==1 else '空'}|{len(es)}|{states['accepted']}|{states['rejected']}|{states['skipped']}|")
    lines += ["", "## 全部訊號：固定時間成本後平均變化", "", "此為事件均值，非年度收益。N為有完整窗口數；缺失數另列；中位數與非重疊敏感度同時保留。一般成本單邊費10bps／滑價5bps；雙成本20bps／10bps。", "",
        "|年|成本倍數|策略／方向|小時|N|缺完整窗口|平均淨變化|中位數|非重疊N|非重疊平均|", "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for c in cases:
        for g in c['summaries']:
            if g['scope']!='all':
                continue
            label=('短線' if g['sleeve']=='intraday' else '波段')+('多' if g['direction']==1 else '空')
            lines.append(f"|{c['year']}|{c['cost']}|{label}|{g['hours']}|{g['observed_count']}|{g['censored_count']}|{percentage(g['mean_net_return'])}|{percentage(g['median_net_return'])}|{g['nonoverlap_count']}|{percentage(g['nonoverlap_mean_net'])}|")
    lines += ["", "## 成交與未成交選擇：24h事件比較", "", "|年|成本倍數|策略／方向|狀態|可觀察N|24h平均淨變化|", "|---|---:|---|---|---:|---:|"]
    for c in cases:
        for g in c['summaries']:
            if g['hours']!=24 or g['scope'] not in {'accepted','rejected','skipped'}:
                continue
            label=('短線' if g['sleeve']=='intraday' else '波段')+('多' if g['direction']==1 else '空')
            lines.append(f"|{c['year']}|{c['cost']}|{label}|{g['scope']}|{g['observed_count']}|{percentage(g['mean_net_return'])}|")
    lines += ["", "## 保存與限制", "", "data/all-signal-diagnostics.json保存全部原策略指標（含CAGR、Sharpe、Sortino、PF、平均盈虧、曝險、費用、滑價、funding）、逐筆訊號、精確准入原因、每個固定窗口與截尾狀態、當時ATR／ER與開盤gap，以及各分組全部統計；data/all-signal-audit.json保存來源SHA256與完整快照重播證明。", "",
        "拒絕組和成交組是原策略選擇後的不同事件，未隨機分配；不可從拒絕組事後較好便推論放寬風控可改善績效。若想改策略仍需新單項候選與完整風控回測。未成交事件沒有量化下單量或槓桿，1單位名目本金只是比較分母，不是建議持倉。", "",
        "2024／2025與這些分析皆調參，非未見驗證。不足窗口不估填、不擴展資料年度；沒有新候選、沒有宣稱已提升收益。仍有固定BTC選樣、1h盤中路徑、未驗歷史MMR、精度／最小量、深度／滑價與研究部位映射限制。未改live/paper/testnet或下單。"]
    lines += ["", "## 本輪診斷結論", "",
        "一般成本：2024全部116次訊號、101次成交、15次拒絕；2025全部94次、85次成交、8次拒絕及1次退出當根跳過。正常／雙成本各年的原始訊號集合完全相同。2025約90%已成交，增加名額不能創造大量原本不存在的機會。", "",
        "2025全部訊號的短線／波段、多／空四組，在4／12／24h三個固定窗口的平均淨變化皆負。24h平均：短多−0.694%、短空−0.417%、波多−0.292%、波空−0.945%；這是事件名目本金的平均變化，不是策略年收益，也不是勝率或預測。短多三個窗口毛價格平均也都負；波多部分毛價格略正但不足成本，故不能把所有問題都歸咎成本或都歸咎價格方向。", "",
        "2025被拒絕的短空1筆、波多5筆、波空2筆，其24h平均分別−2.495%、−0.458%、−2.937%；退出當根跳過的波空1筆亦負。不能說放寬風控會提升績效。2024則有3筆被拒絕短多的24h平均+0.975%，但波多拒絕組12筆為−0.574%，未提供跨年一致的放寬依據。小樣本、非隨機分配，只描述而不估計政策因果效果。", "",
        "非重疊敏感度不是所有格子都同號：例如2025波多12h的全部平均−0.176%，時間先後選擇的非重疊平均約+0.039%。這顯示單一均值不夠穩健，不能宣稱任何市場普遍無效或某個條件已統計證明。所有非重疊N與均值均保留，不只報支持結論的格子。", "",
        "## 下一步研究決策", "",
        "保持原策略、風控及費率，不新增版本。瓶頸優先定位為2025訊號品質及部分毛變化不足成本，而非大量好訊號被拒絕。下一輪先研究『訊號是否在價格已延伸後追進』：用進場前完成資料衡量相對4h均線／ATR的延伸程度，另把開盤gap視為執行時資訊；先保存跨年與方向分組，再決定是否有一項可測條件。尚未設定過濾門檻或宣稱能改善收益，也不重試已失敗的單純強收盤、延長確認或一般均線回撤。"]
    Path("docs/research/2026-10-28-all-signal-results.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()

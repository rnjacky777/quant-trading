"""Read-only catalog of directional research snapshots, separate from spot runs."""
from hashlib import sha256
import json
from pathlib import Path

from app.backtest.frequency import entry_frequency


FILES=("perpetual-direction-research.json","perpetual-entry-filters.json","perpetual-portfolio-research.json","perpetual-portfolio-overlap.json","perpetual-pa-smc.json","perpetual-pa-smc-exit.json","perpetual-pa-smc-confirmation.json","perpetual-confirmed-efficiency.json","perpetual-sweep-frequency.json","perpetual-directional-pullback.json","perpetual-holding-exit.json","perpetual-pullback-reset.json","perpetual-swing-protection.json","perpetual-sweep-mean-guard.json","perpetual-sweep-structural-stop.json","perpetual-directional-loss-guard.json","perpetual-sweep-context-exit.json","perpetual-sweep-structure-confirm.json","perpetual-swing-failure-exit.json","perpetual-slope-risk-cap.json","perpetual-atr-ablation.json","perpetual-swing-volume.json","perpetual-intraday-protection.json")
VARIANTS={"baseline":"多空突破基準","asia_session":"週一亞洲時段","volume_confirmation":"成交量確認",
    "portfolio_intraday":"短線多部位","portfolio_swing":"波段多部位","portfolio_combined":"短線＋波段共用資金",
    "portfolio_overlap_decay":"同向加倉風險遞減","portfolio_pa_smc":"PA＋SMC掃單確認",
    "portfolio_pa_smc_fast_exit":"PA＋SMC波段快速退出（實驗）",
    "portfolio_pa_smc_confirmation":"PA＋SMC波段延後確認（實驗）",
    "portfolio_confirmed_efficiency":"PA＋SMC確認後效率過濾（實驗）",
    "portfolio_sweep_window":"PA＋SMC延長短線確認（未採用）",
    "portfolio_directional_pullback":"多空趨勢回撤恢復（未採用）",
    "portfolio_holding_48h":"PA＋SMC最長持有48h（未採用）",
    "portfolio_pullback_reset":"回撤空單事件重置（未採用）",
    "portfolio_swing_protection":"波段1R價格保護（未採用）",
    "portfolio_sweep_mean_guard":"短線空單均線位置限制（未採用）",
    "portfolio_sweep_structural_stop":"掃單結構止損（研究候選）",
    "portfolio_directional_loss_guard":"結構止損＋同方向連虧保護（研究候選）",
    "portfolio_sweep_context_exit":"短線移除1H通道退出（未採用）",
    "portfolio_sweep_structure_confirm":"掃單＋3根微結構確認（研究候選）",
    "portfolio_swing_failure_exit":"微結構確認＋波段突破失效退出（研究候選）",
    "portfolio_slope_risk_cap":"慢均線斜率風險上限（取捨候選）",
    "portfolio_sweep_no_atr_floor":"掃單移除1H ATR門檻（未採用）",
    "portfolio_swing_volume":"波段確認成交量（取捨候選）",
    "portfolio_intraday_protection":"短線1R價格保護（未採用）"}
MODES={"both":"多空雙向","long_only":"只做多（對照）","short_only":"只做空（對照）"}


def load_directional_evidence(root: Path) -> list[dict]:
    entries=[]
    for name in FILES:
        path=root/name
        if not path.exists():
            continue
        try:
            payload=json.loads(path.read_text(encoding="utf-8"))
            for row in payload["rows"]:
                mode=row.get("mode",row["config"]["mode"])
                variant=row.get("variant","baseline")
                identity=sha256(json.dumps(row,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
                if row["status"]=="completed":
                    result=row["result"]
                    # A directional artifact must retain side labels, never
                    # silently present short SELLs as ordinary spot exits.
                    if any(t["direction"] not in {-1,1} for t in result["trades"]):
                        raise ValueError("invalid side")
                    result["metrics"]["total_return"]
                entries.append(dict(id=identity,row=row,label=VARIANTS[variant],mode=mode,
                    frequency=entry_frequency(row['result']['trades'],row['year']) if row['status']=='completed' else None,
                    mode_label=MODES[mode],year=row["year"],cost=row["cost_multiplier"],
                    since=f"{row['year']}-01-01",until=f"{row['year']+1}-01-01"))
        except (ValueError,KeyError,TypeError) as exc:
            raise ValueError(f"研究快照格式錯誤：{name}，請檢查保存結果") from exc
    return sorted(entries,key=lambda e:(-e['year'],e['cost'],e['label'],e['mode']))


def directional_equity_points(result: dict) -> str:
    return _series_points([float(p['equity']) for p in result['equity_curve']])


def portfolio_position_points(result: dict) -> str:
    return _series_points([float(p['open_positions']) for p in result.get('portfolio_curve',[])])


def _series_points(values: list[float]) -> str:
    if len(values)<2:
        return ""
    low,high=min(values),max(values)
    span=high-low or 1
    return " ".join(f"{i*900/(len(values)-1):.1f},{260-(v-low)*260/span:.1f}" for i,v in enumerate(values))

"""Evidence-linked research memory; no automatic parameter recommendations."""
from hashlib import sha256
import json
from pathlib import Path


# id, parent file/variant, child file/variant, hypothesis, change, decision, limitation
LESSONS = (
    ("swing_hourly_failure", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit", "perpetual-swing-hourly-failure.json", "portfolio_swing_hourly_failure",
     "固定突破邊界失效以1h完成收盤較早確認可能降低等待4h的損失", "波段凍結邊界改每個完成1h收盤判斷，下一根open退出", "未採用，保留原基準", "改善2025但犧牲2024收益及回撤，2025仍虧；原失效虧損組不是可回收收益，提前截斷原贏家，不掃2h/3h或邊界緩衝"),
    ("swing_short_risk_cap", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit", "perpetual-swing-short-risk-cap.json", "portfolio_swing_short_risk_cap",
     "兩年波段空單負貢獻時限制該袖套方向風險可能減輕損失", "僅波段空單risk倍率取min(原loss brake,0.5)，不重複減半", "保留風險配置研究候選，不取代原基準", "四組收益微升，2024回撤不變、2025改善但仍虧；未改善頻率，會縮小贏家，非獨立驗證或空單普遍無效證據，不掃倍率"),
    ("pa_sweep", "perpetual-portfolio-research.json", "portfolio_combined", "perpetual-pa-smc.json", "portfolio_pa_smc",
     "掃單收回及次根確認可改善短線進場", "只替換短線進場為掃單確認", "保留研究，非獲利方案", "2025仍虧，雙成本2024也虧；不是完整SMC系統"),
    ("overlap_risk", "perpetual-portfolio-research.json", "portfolio_combined", "perpetual-portfolio-overlap.json", "portfolio_overlap_decay",
     "同方向後續部位降低風險可提高穩定度", "新單風險乘1/(1+同方向持倉數)", "未採用為全面升級", "2025虧損縮小，但2024一般成本轉虧；不能直接禁加倉"),
    ("fast_swing_exit", "perpetual-pa-smc.json", "portfolio_pa_smc", "perpetual-pa-smc-exit.json", "portfolio_pa_smc_fast_exit",
     "更快承認突破失敗可減少止損", "波段反向通道10根4h改5根", "未採用", "改善2025、犧牲2024；不再掃附近根數"),
    ("swing_confirmation", "perpetual-pa-smc.json", "portfolio_pa_smc", "perpetual-pa-smc-confirmation.json", "portfolio_pa_smc_confirmation",
     "真正延後成交可避開部分沒有延續的突破", "波段多等一根完成4h同向收盤後才進場", "保留研究，非獲利方案", "2025仍虧；不能用事後分組搭配原進場價假裝成交"),
    ("efficiency", "perpetual-pa-smc-confirmation.json", "portfolio_pa_smc_confirmation", "perpetual-confirmed-efficiency.json", "portfolio_confirmed_efficiency",
     "低方向效率時跳過波段進場可減少部分反覆行情損失", "波段ER20須至少0.3", "保留研究參考，非全面優勝", "2024雙成本退步且2025仍虧；樣本小，不掃門檻"),
    ("sweep_window", "perpetual-confirmed-efficiency.json", "portfolio_confirmed_efficiency", "perpetual-sweep-frequency.json", "portfolio_sweep_window",
     "延長確認等待可增加有品質的交易", "短線掃單確認1h改最多3h", "未採用", "四組收益皆退步；筆數上升不是優勢證據"),
    ("pullback", "perpetual-confirmed-efficiency.json", "portfolio_confirmed_efficiency", "perpetual-directional-pullback.json", "portfolio_directional_pullback",
     "趨勢回撤恢復較常出現並可增加淨收益", "短線替換為4h順勢的1h SMA20回撤恢復", "未採用", "四組皆退步，未扣佣金與funding的成交價差也虧；不是單純費用問題"),
    ("holding_48h", "perpetual-confirmed-efficiency.json", "portfolio_confirmed_efficiency", "perpetual-holding-exit.json", "portfolio_holding_48h",
     "盈利部位可能被24h上限截斷", "短週期最大持有24h改48h", "未採用", "四組收益皆退步；時間退出組盈利不表示延長一定更好"),
    ("short_reset", "perpetual-directional-pullback.json", "portfolio_directional_pullback", "perpetual-pullback-reset.json", "portfolio_pullback_reset",
     "空單等待新4h均線回撤事件可減少重複損失", "重置後只發第一個合格短線空單", "未採用為策略替代", "改善失敗父版本但全部仍虧、都不如原掃單參考；首次組本身也虧"),
    ("swing_price_protection", "perpetual-confirmed-efficiency.json", "portfolio_confirmed_efficiency", "perpetual-swing-protection.json", "portfolio_swing_protection",
     "波段完成收盤達+1R後保護價格可減少盈利回吐", "只將波段止損於+1R後移至進場價、下一根生效", "未採用為全面升級", "改善2025卻犧牲2024；價格保本不是扣費後保本，會截斷原贏家"),
    ("short_mean_guard", "perpetual-confirmed-efficiency.json", "portfolio_confirmed_efficiency", "perpetual-sweep-mean-guard.json", "portfolio_sweep_mean_guard",
     "短線掃單空單不在4h均線下方追進可改善訊號品質", "僅短線空單需close至少為完成4h SMA20", "未採用", "三組收益退步，僅2025雙成本微升；事件分組較好不等於有止損及共享資金的策略較好"),
    ("sweep_structural_stop", "perpetual-confirmed-efficiency.json", "portfolio_confirmed_efficiency", "perpetual-sweep-structural-stop.json", "portfolio_sweep_structural_stop",
     "止損改以已知掃單形態失效位置可改善不相符的ATR止損", "短線初始止損由2ATR改為掃單low／high，風險預算不變", "保留下一輪研究候選", "四組收益微升但回撤都增加、2025仍虧；非獨立驗證或穩定獲利證據"),
    ("directional_loss_guard", "perpetual-sweep-structural-stop.json", "portfolio_sweep_structural_stop", "perpetual-directional-loss-guard.json", "portfolio_directional_loss_guard",
     "相反方向盈利不應解除當前方向尚未恢復的連虧減倉", "風險倍率取原共享與同方向連虧倍率較小者", "保留下一輪研究候選", "四組收益及回撤改善但2025仍虧；屬風險配置改善，非訊號正期望或未見驗證"),
    ("context_only_exit", "perpetual-directional-loss-guard.json", "portfolio_directional_loss_guard", "perpetual-sweep-context-exit.json", "portfolio_sweep_context_exit",
     "結構與4h方向未失效時1h通道可能過早退出", "短線移除1h通道退出，保留結構stop／4h反轉／24h上限", "未採用", "僅2025一般成本收益微升，其他三組收益及全部回撤退步；虧損退出組不能直接當可回收收益"),
    ("microstructure_confirmation", "perpetual-directional-loss-guard.json", "portfolio_directional_loss_guard", "perpetual-sweep-structure-confirm.json", "portfolio_sweep_structure_confirm",
     "借用公開掃單後結構確認概念，排除只越過單根掃單bar的較弱確認", "短線確認close還須越過之前3根完成bar的高／低", "保留下一輪研究候選", "四組收益及回撤改善但2025仍虧；短線18／16筆，頻率不足，非原作者策略複現或未見驗證"),
    ("swing_breakout_failure", "perpetual-sweep-structure-confirm.json", "portfolio_sweep_structure_confirm", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit",
     "波段完成4h收盤回到進場時突破區間代表該次突破失效", "每lot固定20根突破邊界，4h收盤失效後下一1h開盤退出", "保留下一輪研究候選", "四組收益及回撤改善但2025仍虧；短線頻率未提升，調參結果不是未見驗證"),
    ("directional_slope_cap", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit", "perpetual-slope-risk-cap.json", "portfolio_slope_risk_cap",
     "慢均線本身斜率不支持方向時限制新單風險可減少不利曝險", "原loss brake與完成4h SMA60的24h方向斜率0.5上限取min", "保留取捨候選，不取代原研究基準", "四組收益小升但2024一般回撤增加；2025仍虧且正常成本僅改善約1.8 USDT；同入出場路徑只是數量改變，不掃斜率參數"),
    ("hourly_atr_ablation", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit", "perpetual-atr-ablation.json", "portfolio_sweep_no_atr_floor",
     "結構止損已替換ATR止損後，舊固定ATR門檻可能錯排除完整掃單形態", "只移除短線ATR14/close至少0.006，保留形態與所有風控", "未採用，保留父基準與ATR門檻", "四組收益與回撤皆退步；新增低ATR7/13筆一般成本合計約虧130/97 USDT，放寬不解決頻率與優勢，不掃附近門檻"),
    ("swing_confirmation_volume", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit", "perpetual-swing-volume.json", "portfolio_swing_volume",
     "低參與量的波段確認可能缺乏延續", "波段完成確認bar成交量至少為前20根4h平均量", "保留取捨候選，不取代原研究基準", "四組收益小升但2024兩組回撤退步；2025仍虧，正常成本僅改善約2 USDT；少量調參分組不能證明優勢或滿足頻率"),
    ("intraday_price_protection", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit", "perpetual-intraday-protection.json", "portfolio_intraday_protection",
     "目前結構掃單短線有達1R後轉虧案例，可與舊波段失敗實驗分開測試", "只對短線完成收盤達1R後移stop至進場價，下一根生效", "未採用為研究基準", "三組收益微升但2025雙成本收益與回撤退步；價格保護仍扣費且會將原小贏家退出成虧損，不掃1R附近參數"),
    ("swing_long_signal_hold", "perpetual-swing-failure-exit.json", "portfolio_swing_failure_exit", "perpetual-swing-long-signal-hold.json", "portfolio_swing_long_signal_hold",
     "訊號出場的波段多單同筆固定72h兩年都較好，訊號出場可能過早", "波段多單進場未滿72h忽略exit_long；止損、突破失效與168h上限不變", "未採用，保留原基準", "2025改善約0.57點但2024四組皆微退、2025回撤增加；2025約41/57 USDT改善來自單筆多單轉盈解除共享連虧減倉使空單加倍，路徑脆弱；不掃48/96h"),
)


def research_lessons(root: Path) -> dict:
    cache: dict[str, dict] = {}
    hashes: dict[str, str] = {}
    def rows(name: str, variant: str) -> dict:
        if name not in cache:
            path=root/name
            content=path.read_bytes()
            hashes[name]=sha256(content).hexdigest()
            cache[name]=json.loads(content)
        found=[r for r in cache[name]['rows'] if r.get('variant')==variant]
        result={(r['year'],r['cost_multiplier']):r for r in found}
        if len(found)!=4 or len(result)!=4 or set(result)!={(2024,1),(2024,2),(2025,1),(2025,2)}:
            raise ValueError(f"{name}: all four unique period/cost cases required")
        return result
    lessons=[]
    for identity,pfile,pvariant,cfile,cvariant,hypothesis,change,decision,limitation in LESSONS:
        parents,children=rows(pfile,pvariant),rows(cfile,cvariant)
        comparisons=[]
        for key in sorted(parents):
            parent,child=parents[key],children[key]
            if parent['status']!='completed' or child['status']!='completed':
                raise ValueError(f"{identity}: failed evidence requires explicit review")
            if parent['input_fingerprints']!=child['input_fingerprints']:
                raise ValueError(f"{identity}: mismatched market/funding/mark evidence")
            p,c=parent['result']['metrics'],child['result']['metrics']
            comparisons.append(dict(year=key[0],cost=key[1],parent_metrics=p,child_metrics=c,
                return_delta=c['total_return']-p['total_return'],
                target_met=c['total_return']>=.1 and c['maximum_drawdown']>=-.1))
        lessons.append(dict(id=identity,parent=pvariant,child=cvariant,hypothesis=hypothesis,
            one_change=change,decision=decision,limitation=limitation,comparisons=comparisons,
            used_for_tuning=True,independent_validation=False))
    budget_path = root / "perpetual-risk-budget-055.json"
    if budget_path.exists():
        content = budget_path.read_bytes()
        budget = json.loads(content)
        if budget.get('status') != 'completed' or len(budget['rows']) != 32:
            raise ValueError("risk-budget experiment incomplete; inspect saved failure before further tuning")
        expected = {(variant, year, fee, slip) for variant in (budget['parent'], budget['candidate'])
                    for year in range(2022, 2026) for fee, slip in ((5, 5), (10, 5), (10, 10), (20, 10))}
        actual = {(r['variant'], r['year'], r['fee_bps'], r['slippage_bps']) for r in budget['rows']}
        if actual != expected:
            raise ValueError('risk-budget missing or duplicated period/cost evidence')
        hashes[budget_path.name] = sha256(content).hexdigest()
        comparisons = []
        for child in budget['rows']:
            if child['variant'] != budget['candidate']:
                continue
            key = (child['year'], child['fee_bps'], child['slippage_bps'])
            parent = next(r for r in budget['rows'] if r['variant'] == budget['parent']
                          and (r['year'], r['fee_bps'], r['slippage_bps']) == key)
            if parent['input_fingerprints'] != child['input_fingerprints']:
                raise ValueError('risk-budget parent/child inputs differ')
            comparisons.append(dict(year=key[0], fee_bps=key[1], slippage_bps=key[2],
                parent_metrics=parent['result']['metrics'], child_metrics=child['result']['metrics']))
        lessons.append(dict(id='uniform_risk_budget_055', parent=budget['parent'], child=budget['candidate'],
            hypothesis='Uniform risk increase may meet Objective A while retaining risk headroom',
            one_change='Both sleeve risk_per_trade 0.0025 to 0.0055; all admission limits unchanged',
            decision=budget['decision'], comparisons=comparisons, objectives=budget['objectives'],
            limitation='Mean 4.299% misses 5%; admission competition removes winners and changes loss-brake paths. Follow-up admission-risk diagnosis reproduced 32 cases: giveback is 72–82% of primary-cost blocked risk, but 21 missing parent trades include 10 losers and only +70.64 USDT original net PnL. Giveback is real equity drawdown risk; insufficient evidence to remove it. See docs/research/2026-10-29-admission-risk-results.md. Do not sweep nearby budgets. All four years are tuning evidence.',
            used_for_tuning=True, independent_validation=False))
    return dict(scope="BTC perpetual 1h/4h research; not automatically applicable to spot or other assets",
        evidence_status="saved snapshots checked, not an engine replay; original replay audits remain required",
        warning="Overlapping periods/cost cases are not independent. No proven profitable candidate; no automatic optimization or orders.",
        lessons=lessons,source_sha256=hashes)

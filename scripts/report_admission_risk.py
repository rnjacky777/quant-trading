"""Render complete diagnostic evidence, without a new strategy simulation."""
import json
from pathlib import Path

from scripts.diagnose_admission_risk import OUTPUT


def main() -> None:
    data=json.loads(OUTPUT.read_text(encoding='utf-8'))
    if data['status']!='completed' or len(data['rows'])!=32:
        raise ValueError('complete diagnostic required')
    primary=[r for r in data['rows'] if r['variant']=='portfolio_risk_budget_055' and
             (r['fee_bps'],r['slippage_bps'])==(5,5)]
    missing=sum(r['missing_parent_trades']['parent_net_pnl'] for r in primary)
    text=['# 總止損風險准入診斷結果', '', '2026-10-29。**決定：證據不足，保留原基準，不放寬准入限制、不建立新候選。**', '',
          '新增可選唯讀 admission_observer 與獨立診斷腳本；每次准入前複製持倉、擬議部位及預算。32個既有案例均重現輸入指紋及完整結果，原交易、年度績效與風控規則不變。', '',
          '## 主要發現', '',
          '現行風險是由當前mark到止損的潛在損失，包含剩餘入場至止損損失、未實現獲利回吐及未來費用／funding預留。浮盈回吐屬於當前淨值可能發生的回撤，不是虛構風險或已證實的引擎錯誤。', '',
          '|年度|0.55%版本遭風險拒絕次數|浮盈回吐占被拒事件風險|局部忽略回吐可解鎖次數|缺少父交易（贏／輸）|缺少交易原淨損益 USDT|',
          '|---|---:|---:|---:|---:|---:|']
    for r in primary:
        s,m=r['summary'],r['missing_parent_trades']
        text.append(f"|{r['year']}|{s['blocked']}|{s['giveback_event_weighted_share']*100:.1f}%|{s['local_unblocked']}|{m['count']}（{m['winners']}/{m['losers']}）|{m['parent_net_pnl']:+.2f}|")
    text += ['', '浮盈占比是被拒事件風險金額的加權比例，同一持倉可能在多次事件中出現，不是獨立樣本或時間占比。解鎖數只是凍結當下其他狀態的局部計算，沒有實際放入新單，不能相加當作可執行交易數或收益。', '',
             f'主要成本四年缺少的父交易原淨損益合計 {missing:+.2f} USDT；不只漏掉贏家，也避開輸家。A的平均收益差距0.701082個百分點，相當於四個獨立10,000 USDT年度合計尚差280.43 USDT。前述{missing:.2f}不是可回收收益，也不是上限：只涵蓋父版本曾成交的子集，沒有替新增訊號、部分成交、部位重配及後續連虧路徑定價。它不足以支持「移除回吐就能達標」的說法。', '',
             '## 為什麼不直接修改風險定義', '',
             '- 主成本2022與2025缺少的父交易合計為負，放回全部被擋單不一定改善這兩年。2023／2024較好，也不能據此只挑趨勢年份或已知贏家。',
             '- 已有風險放大候選的20/10成本2025收益為−2.791%，距−3%底線僅約20.88 USDT。這不是新增部位可用預算；更多同方向持倉會改變完整風險路徑。',
             '- 將浮盈回吐從風險預算排除，會允許更多對當前淨值的總損失，而A衡量的回撤正是淨值回撤。需要先建立雙重風險預算的明確含義與依據；不能為了容納既有贏家而挑一個新上限。',
             '- 先前移動止損保護波段盈利的實驗也曾犧牲2024收益；這份診斷沒有提供重做同一失敗規則的新證據。', '',
             '## 全部年度／成本／版本診斷', '',
             '|版本|年|費率/滑價 bps|拒絕|部分准入|回吐占比|局部解鎖|局部增加部分量|',
             '|---|---|---|---:|---:|---:|---:|---:|']
    for r in data['rows']:
        s=r['summary']
        text.append(f"|{'基準0.25%' if r['variant']=='portfolio_swing_failure_exit' else '候選0.55%'}|{r['year']}|{r['fee_bps']}/{r['slippage_bps']}|{s['blocked']}|{s['partial']}|{s['giveback_event_weighted_share']*100:.1f}%|{s['local_unblocked']}|{s['local_partial_increased']}|")
    text += ['', '## 所有缺少的父交易比較（不跨成本加總）', '',
             '|年度|費率/滑價|缺少交易|贏家|輸家|原淨損益 USDT|', '|---|---|---:|---:|---:|---:|']
    for r in data['rows']:
        if 'missing_parent_trades' not in r:
            continue
        m=r['missing_parent_trades']
        text.append(f"|{r['year']}|{r['fee_bps']}/{r['slippage_bps']}|{m['count']}|{m['winners']}|{m['losers']}|{m['parent_net_pnl']:+.2f}|")
    text += ['', '## 逐筆事件與限制', '',
             'data/admission-risk-diagnostics.json 保存全部有效擬議部位的准入前狀態、各持倉拆解、局部假設比例、年度成本指標，以及逐筆缺少父交易。每日上限／無效進場在觀察器之前被拒的事件，另由 all_admission_counts 完整保留。', '',
             '既有年度收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險及成本均完整重現，見 [風險預算結果](2026-10-29-risk-budget-results.md)。其月度淨值、多空／短線／波段及頻率結論不變；本輪不是新的收益比較。', '',
             '全部四年屬調參證據。觀察器在當下決策前讀取持倉；未來交易結果只用於事後診斷，沒有送入訊號或風控。固定滑價、流動性／延遲簡化、歷史保證金級距未驗證等既有限制不變；研究lot不代表交易所hedge mode支援。', '',
             '策略回測：32次既有案例重播；程式測試：全套290通過（含7個新增診斷測試案例）；研究候選：0。新測試覆蓋多空對稱、已發生損失不重複計算、未來費用保留、相反部位不抵銷、拆解不一致拒絕，以及觀察器修改副本不影響交易。', '',
             '測試環境：沙盒內的全套執行卡在Windows asyncio建立socketpair；取得自動核准後在沙盒外重跑，全套290通過（5.96秒）。唯一警告為既有Starlette/httpx棄用提示。', '',
             '下一項可做的工作是事前定義前瞻paper觀察方案，或另行提出有經濟機制的新訊號假說；本診斷不授權繼續掃風險上限或自動啟動paper／testnet。']
    Path('docs/research/2026-10-29-admission-risk-results.md').write_text('\n'.join(text)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()

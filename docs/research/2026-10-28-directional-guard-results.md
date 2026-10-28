# 結構止損＋同方向連虧保護：四組收益與回撤均改善

2026-10-28。portfolio_sweep_structural_stop → portfolio_directional_loss_guard，唯一risk變更：min(原共享連虧倍率，同策略同方向連虧倍率)。不是重複減半成1/4，不取消共享保護、不把反向盈利視為當前方向已恢復。

## 診斷依據

止損較窄多單組雖虧，但相對舊ATR未跨年／成本一致較差，故未直接加ATR下限。轉而逐筆重建當時已知平倉紀錄，101／101／85／85次原planned risk全重現一致；額外同方向保護對父案例分別影響6／5／10／8筆，凍結父損益−91.44／−74.44／−64.10／−37.93USDT，但也有贏家，故僅作一次可反駁假說，不把群組除半假裝可得收益。

## 不變條件

結構stop、全部多空進出場、波段、24h／168h持有、每年10,000本金、原risk上限0.25%（保護後0.125%）、gross/stoprisk/reserved-margin與每日總計≤2全部不變。一般單邊費10bps／滑價5bps，雙成本20bps／10bps，另含實際funding，全部實際1x。父四筆行情／mark／funding指紋及整份回測快照逐一一致後才執行候選；guard預設關閉行為不變。

## 相較直接父版本

|年|成本倍數|父淨收益|候選淨收益|父最大回撤|候選最大回撤|交易數|額外保護筆數|
|---|---:|---:|---:|---:|---:|---:|---:|
|2024|1|+3.104%|+3.570%|-3.171%|-3.081%|101|6|
|2024|2|-0.046%|+0.328%|-4.235%|-3.877%|101|5|
|2025|1|-2.779%|-2.454%|-4.655%|-4.381%|85|10|
|2025|2|-3.807%|-3.617%|-4.909%|-4.895%|85|8|

## 判斷與下一輪基準

相較直接父結構止損版本，四組收益提高、回撤降低。一般2024約+3.104%→+3.570%、2025−2.779%→−2.454%；雙成本2024−0.046%→+0.328%、2025−3.807%→−3.617%。交易筆數與實際進出場事件完全一致，只改變風險配置；可以保留下一輪研究候選，父與較早原版都繼續作對照。

2025一般成本成交價差損益（仍含滑價、未扣費/funding）由−121.62改善至−99.18USDT，費用由151.10降至141.02；不是調低費率，亦不只是省費。但同事件退出與每單位qty結果完全相同，因此不是新訊號優勢，只是依過去已平倉紀錄重配風險的歷史改善。2025仍負，兩年各淨10%目標未達，不能用槓桿放大或推實盤。

相較更早原掃單＋波段效率參考，2024／2025一般成本淨收益較高，但回撤仍略高（原約2.970%／4.292%，本候選3.081%／4.381%），不能省略這個較早風險對照或宣稱所有版本都更穩。

## 驗證與限制

234項pytest通過：多空鏡像跨UTC日的兩次同方向虧損→相反盈利→同方向再進場，原共享保護仍有效、同方向未恢復不能被解除、不重複相乘、零PnL不重置，observer深拷貝不污染risk trace。四筆父整份快照一致、候選逐筆已知歷史重建與trace／_open數量及risk完全一致，並核對現金、ID、每日≤2、1x、單筆與總gross/stoprisk/margin預算。計劃risk不是跳空或未來funding下的保證最大損失。

方向保護在相同已知歷史下只維持／降低預算，但實際帳戶路徑會受數量改變影響，不能保證每個相同時間qty都較父低。會壓低部分原贏家；逐筆共同事件及保護群組贏家數都保存，不只報收益提升。

2024／2025及13項經驗均調參，非未見驗證；成本案例與訊號事件重疊，四組同向不是四份獨立統計證據，不掃連虧次數／倍率。保留固定BTC選樣、1h盤中路徑、MMR2%非歷史級距、深度滑價、精度／最小量與研究部位／交易所映射限制。只完成研究風控，未宣稱paper/testnet/live能力、未改交易設定、未下單。完整曲線交易data/perpetual-directional-loss-guard.json，逐筆trace及來源審計data/directional-loss-guard-audit.json。

## 2024／成本1倍完整指標與減倉代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率、較早原版參考與原贏家被減少的對照：

```json
{
  "year": 2024,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -14.541177225026088,
    "average_win": 33.50253895622429,
    "cagr": 0.035625787400684006,
    "exposure": 0.30096755833807626,
    "fees": 179.18870198633135,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.03080606961729604,
    "maximum_margin_ratio": 0.02325297997566693,
    "net_funding": -41.567534682436786,
    "number_of_trades": 101,
    "profit_factor": 1.3897004573662375,
    "sharpe_ratio": 1.0372549368146968,
    "slippage": 89.59451783142286,
    "sortino_ratio": 1.5275050455411683,
    "total_return": 0.03570023151598756,
    "win_rate": 0.37623762376237624
  },
  "reference_original_metrics": {
    "average_loss": -15.11828530619079,
    "average_win": 31.863824096076215,
    "cagr": 0.03047202842589769,
    "exposure": 0.30096755833807626,
    "fees": 168.23863728510398,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.02969728199849264,
    "maximum_margin_ratio": 0.023252979975666933,
    "net_funding": -41.196495046053386,
    "number_of_trades": 101,
    "profit_factor": 1.3257702719446494,
    "sharpe_ratio": 0.9091562217951892,
    "slippage": 84.11946837005519,
    "sortino_ratio": 1.3333626949030122,
    "total_return": 0.030535545076314063,
    "win_rate": 0.38613861386138615
  },
  "frequency": {
    "total": 101,
    "calendar_days": 366,
    "daily_average": 0.27595628415300544,
    "active_days": 85,
    "zero_entry_days": 281,
    "intraday": 60,
    "intraday_daily_average": 0.16393442622950818,
    "intraday_active_days": 55,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 40,
        "daily_average": 0.1092896174863388
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 20,
        "daily_average": 0.0546448087431694
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 33,
        "daily_average": 0.09016393442622951
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 8,
        "daily_average": 0.02185792349726776
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 11,
      "pnl": -197.39841094353355
    },
    "intraday/-1/stop_loss": {
      "count": 4,
      "pnl": -82.8345516160078
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -84.26224194218537
    },
    "intraday/1/time_limit": {
      "count": 13,
      "pnl": 331.6111087653527
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -26.21703175035529
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 620.1323996796552
    },
    "intraday/1/stop_loss": {
      "count": 19,
      "pnl": -340.27293400800005
    },
    "intraday/1/signal": {
      "count": 8,
      "pnl": 0.76839083728406
    },
    "intraday/-1/signal": {
      "count": 9,
      "pnl": -48.99366157727643
    },
    "intraday/-1/time_limit": {
      "count": 7,
      "pnl": 194.83427815403198
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -10.365030439086135
    }
  },
  "exact_entry_exit_and_unit_pnl_matches": 101,
  "past_only_brake_trace_checks": 101,
  "parent_price_pnl_before_fees_funding": 539.6072951572261,
  "child_price_pnl_before_fees_funding": 577.7585518286476,
  "parent_fees": 187.52710127786145,
  "child_fees": 179.18870198633135,
  "extra_guard_count": 6,
  "protected_parent_winners": 1,
  "parent_pnl_in_guard_cohort": -91.44400148640611,
  "child_pnl_in_guard_cohort": -45.77966108158543,
  "common_events": [
    {
      "entry_timestamp_ms": 1704744000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.44130449432212,
      "child_pnl": -24.44130449432212,
      "parent_quantity": 0.014839399386279178,
      "child_quantity": 0.014839399386279178
    },
    {
      "entry_timestamp_ms": 1706061600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.231804563981935,
      "child_pnl": -23.231804563981935,
      "parent_quantity": 0.038731409466935936,
      "child_quantity": 0.038731409466935936
    },
    {
      "entry_timestamp_ms": 1705968000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.232750533840917,
      "child_pnl": -23.232750533840917,
      "parent_quantity": 0.02148038050568708,
      "child_quantity": 0.02148038050568708
    },
    {
      "entry_timestamp_ms": 1706486400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 47.45373136299877,
      "child_pnl": 47.45373136299877,
      "parent_quantity": 0.042143531928082206,
      "child_quantity": 0.042143531928082206
    },
    {
      "entry_timestamp_ms": 1706572800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.183954938509274,
      "child_pnl": -12.183954938509274,
      "parent_quantity": 0.010838953514042094,
      "child_quantity": 0.010838953514042094
    },
    {
      "entry_timestamp_ms": 1706443200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -6.87491331187834,
      "child_pnl": -6.87491331187834,
      "parent_quantity": 0.01097860912935626,
      "child_quantity": 0.01097860912935626
    },
    {
      "entry_timestamp_ms": 1707177600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 11.144876965601142,
      "child_pnl": 11.144876965601142,
      "parent_quantity": 0.04510381218171524,
      "child_quantity": 0.04510381218171524
    },
    {
      "entry_timestamp_ms": 1707350400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 83.43645643827757,
      "child_pnl": 83.43645643827757,
      "parent_quantity": 0.011493894621415965,
      "child_quantity": 0.011493894621415965
    },
    {
      "entry_timestamp_ms": 1707364800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 86.55143471554155,
      "child_pnl": 86.55143471554155,
      "parent_quantity": 0.011361934444978721,
      "child_quantity": 0.011361934444978721
    },
    {
      "entry_timestamp_ms": 1707465600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 51.57428165886777,
      "child_pnl": 51.57428165886777,
      "parent_quantity": 0.009639416214969861,
      "child_quantity": 0.009639416214969861
    },
    {
      "entry_timestamp_ms": 1708398000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.021143279106766,
      "child_pnl": -24.021143279106766,
      "parent_quantity": 0.04080695593557443,
      "child_quantity": 0.04080695593557443
    },
    {
      "entry_timestamp_ms": 1708455600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 2.2663965922392957,
      "child_pnl": 2.2663965922392957,
      "parent_quantity": 0.02669560804706133,
      "child_quantity": 0.02669560804706133
    },
    {
      "entry_timestamp_ms": 1709020800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 121.24854600562938,
      "child_pnl": 121.24854600562938,
      "parent_quantity": 0.013082245105395102,
      "child_quantity": 0.013082245105395102
    },
    {
      "entry_timestamp_ms": 1709121600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 15.88073480758657,
      "child_pnl": 15.88073480758657,
      "parent_quantity": 0.009741028918003282,
      "child_quantity": 0.009741028918003282
    },
    {
      "entry_timestamp_ms": 1710158400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -26.613304281725473,
      "child_pnl": -26.613304281725473,
      "parent_quantity": 0.011259861707871209,
      "child_quantity": 0.011259861707871209
    },
    {
      "entry_timestamp_ms": 1710172800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -26.0616157872382,
      "child_pnl": -26.0616157872382,
      "parent_quantity": 0.010633463510995355,
      "child_quantity": 0.010633463510995355
    },
    {
      "entry_timestamp_ms": 1710270000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 11.382170011920993,
      "child_pnl": 11.382170011920993,
      "parent_quantity": 0.008116017487367242,
      "child_quantity": 0.008116017487367242
    },
    {
      "entry_timestamp_ms": 1710450000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -25.214335416233528,
      "child_pnl": -25.214335416233528,
      "parent_quantity": 0.010302340821260136,
      "child_quantity": 0.010302340821260136
    },
    {
      "entry_timestamp_ms": 1711220400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -1.281240045463909,
      "child_pnl": -1.281240045463909,
      "parent_quantity": 0.029041366783277178,
      "child_quantity": 0.029041366783277178
    },
    {
      "entry_timestamp_ms": 1711404000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.093514028905238,
      "child_pnl": -6.093514028905238,
      "parent_quantity": 0.007971515933004472,
      "child_quantity": 0.007971515933004472
    },
    {
      "entry_timestamp_ms": 1712260800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 1.86341489174968,
      "child_pnl": 1.86341489174968,
      "parent_quantity": 0.011409409214779577,
      "child_quantity": 0.011409409214779577
    },
    {
      "entry_timestamp_ms": 1712577600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.602591470508099,
      "child_pnl": -12.602591470508099,
      "parent_quantity": 0.005871889985656219,
      "child_quantity": 0.005871889985656219
    },
    {
      "entry_timestamp_ms": 1713830400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.389703340974355,
      "child_pnl": -12.389703340974355,
      "parent_quantity": 0.006484757081171501,
      "child_quantity": 0.006484757081171501
    },
    {
      "entry_timestamp_ms": 1713996000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.12021441253937,
      "child_pnl": -24.12021441253937,
      "parent_quantity": 0.02446218522712702,
      "child_quantity": 0.02446218522712702
    },
    {
      "entry_timestamp_ms": 1714154400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": -23.912865081610533,
      "child_pnl": -11.956432540805267,
      "parent_quantity": 0.026859659052170675,
      "child_quantity": 0.013429829526085338
    },
    {
      "entry_timestamp_ms": 1714280400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 17.77561258655057,
      "child_pnl": 17.79653009576907,
      "parent_quantity": 0.0160154404719522,
      "child_quantity": 0.01603428669297999
    },
    {
      "entry_timestamp_ms": 1714507200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -2.973979730485447,
      "child_pnl": -2.9774793706877305,
      "parent_quantity": 0.005245380997406068,
      "child_quantity": 0.005251553516346478
    },
    {
      "entry_timestamp_ms": 1715216400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": -23.474454730872694,
      "child_pnl": -11.751039185446535,
      "parent_quantity": 0.0330790489071782,
      "child_quantity": 0.016558987392126
    },
    {
      "entry_timestamp_ms": 1715259600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": 28.37764415892065,
      "child_pnl": 14.221942757862058,
      "parent_quantity": 0.02159310650253859,
      "child_quantity": 0.010821755425634431
    },
    {
      "entry_timestamp_ms": 1715817600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -2.2658244608944598,
      "child_pnl": -2.2679481365816874,
      "parent_quantity": 0.00572976040024187,
      "child_quantity": 0.005735130698367625
    },
    {
      "entry_timestamp_ms": 1716249600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.389720582384774,
      "child_pnl": -12.401333021400449,
      "parent_quantity": 0.005831677352843438,
      "child_quantity": 0.005837143174059395
    },
    {
      "entry_timestamp_ms": 1716501600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 7.762456199919796,
      "child_pnl": 7.769731670632316,
      "parent_quantity": 0.011920693976430478,
      "child_quantity": 0.01193186681369548
    },
    {
      "entry_timestamp_ms": 1716926400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.992594458945007,
      "child_pnl": -12.00383468594352,
      "parent_quantity": 0.017354600500493537,
      "child_quantity": 0.01737086634269823
    },
    {
      "entry_timestamp_ms": 1717426800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.936307258881477,
      "child_pnl": -12.948431993909427,
      "parent_quantity": 0.013878012469829818,
      "child_quantity": 0.013891019831246328
    },
    {
      "entry_timestamp_ms": 1718121600000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.083157110554039,
      "child_pnl": -12.094482218665242,
      "parent_quantity": 0.007631415387876128,
      "child_quantity": 0.0076385680387535786
    },
    {
      "entry_timestamp_ms": 1718107200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.954642753020158,
      "child_pnl": -11.965847409251143,
      "parent_quantity": 0.008401841904878382,
      "child_quantity": 0.008409716648791367
    },
    {
      "entry_timestamp_ms": 1719244800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.023447686362955,
      "child_pnl": -12.034716830980672,
      "parent_quantity": 0.009174277755773504,
      "child_quantity": 0.009182876475998334
    },
    {
      "entry_timestamp_ms": 1720090800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.050719639353684,
      "child_pnl": -12.062014344991024,
      "parent_quantity": 0.010174783114057059,
      "child_quantity": 0.010184319571931472
    },
    {
      "entry_timestamp_ms": 1720166400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.376601524143181,
      "child_pnl": -12.38820166713791,
      "parent_quantity": 0.0038440794269882666,
      "child_quantity": 0.0038476823442308693
    },
    {
      "entry_timestamp_ms": 1720314000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 42.66342567585064,
      "child_pnl": 42.70341256865959,
      "parent_quantity": 0.01587439878476743,
      "child_quantity": 0.01588927728719796
    },
    {
      "entry_timestamp_ms": 1720436400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.58387162903898,
      "child_pnl": -12.59566603884036,
      "parent_quantity": 0.015544646031772838,
      "child_quantity": 0.01555921546882058
    },
    {
      "entry_timestamp_ms": 1720512000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.624457168544218,
      "child_pnl": -23.64659952166057,
      "parent_quantity": 0.029019836208935654,
      "child_quantity": 0.02904703545656842
    },
    {
      "entry_timestamp_ms": 1721088000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -6.0663863913664615,
      "child_pnl": -6.0720721969136,
      "parent_quantity": 0.002762965029172787,
      "child_quantity": 0.0027655546568153286
    },
    {
      "entry_timestamp_ms": 1721124000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 23.451654875490775,
      "child_pnl": 23.473635267239505,
      "parent_quantity": 0.01199925677460917,
      "child_quantity": 0.01201050324595628
    },
    {
      "entry_timestamp_ms": 1720958400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 23.237555043556686,
      "child_pnl": 23.259334767241516,
      "parent_quantity": 0.007220065947413603,
      "child_quantity": 0.007226833055270956
    },
    {
      "entry_timestamp_ms": 1721016000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 4.456941897920554,
      "child_pnl": 4.461119229091331,
      "parent_quantity": 0.00651448295406735,
      "child_quantity": 0.0065205887443892325
    },
    {
      "entry_timestamp_ms": 1721030400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 3.196690555789408,
      "child_pnl": 3.199686698751975,
      "parent_quantity": 0.0065630733769614594,
      "child_quantity": 0.006569224709337245
    },
    {
      "entry_timestamp_ms": 1721336400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 87.35111469040059,
      "child_pnl": 87.43298574516315,
      "parent_quantity": 0.03017127128255775,
      "child_quantity": 0.030199549728828132
    },
    {
      "entry_timestamp_ms": 1721592000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -7.2813957440046035,
      "child_pnl": -7.28822033407215,
      "parent_quantity": 0.013399610469120728,
      "child_quantity": 0.013412169441566616
    },
    {
      "entry_timestamp_ms": 1721725200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.677760930004958,
      "child_pnl": -23.699953242817752,
      "parent_quantity": 0.028090378096127317,
      "child_quantity": 0.02811670619613567
    },
    {
      "entry_timestamp_ms": 1721919600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 17.450449372923444,
      "child_pnl": 17.466805050825283,
      "parent_quantity": 0.009425334325146216,
      "child_quantity": 0.009434168351654346
    },
    {
      "entry_timestamp_ms": 1722027600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -23.83925122003894,
      "child_pnl": -11.930797445943103,
      "parent_quantity": 0.025263642675000066,
      "child_quantity": 0.012643660688836754
    },
    {
      "entry_timestamp_ms": 1722117600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.780736707223651,
      "child_pnl": -10.803460266733708,
      "parent_quantity": 0.01029002297679538,
      "child_quantity": 0.01031171221342393
    },
    {
      "entry_timestamp_ms": 1722279600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.08552389106516,
      "child_pnl": -12.110997671643148,
      "parent_quantity": 0.009850447597587662,
      "child_quantity": 0.009871210300384634
    },
    {
      "entry_timestamp_ms": 1722376800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.143655904876203,
      "child_pnl": -12.169252215695966,
      "parent_quantity": 0.009978383057279576,
      "child_quantity": 0.009999415421520908
    },
    {
      "entry_timestamp_ms": 1722844800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -25.039708047585663,
      "child_pnl": -12.546243282309485,
      "parent_quantity": 0.00630716929406333,
      "child_quantity": 0.003160231750132589
    },
    {
      "entry_timestamp_ms": 1723032000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -0.9135890558402346,
      "child_pnl": -0.9166459228097008,
      "parent_quantity": 0.012795434129520682,
      "child_quantity": 0.012838247623947386
    },
    {
      "entry_timestamp_ms": 1723165200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 3.485866535793677,
      "child_pnl": 3.497530237547892,
      "parent_quantity": 0.007046688895121014,
      "child_quantity": 0.007070267100649963
    },
    {
      "entry_timestamp_ms": 1723255200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.864955466674873,
      "child_pnl": -12.908001579342633,
      "parent_quantity": 0.020056632625957038,
      "child_quantity": 0.020123742074566422
    },
    {
      "entry_timestamp_ms": 1723712400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": -23.555366565218925,
      "child_pnl": -11.817091384943097,
      "parent_quantity": 0.028204975797936113,
      "child_quantity": 0.014149674792429694
    },
    {
      "entry_timestamp_ms": 1723759200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 1.9859198580026773,
      "child_pnl": 1.9948885714188376,
      "parent_quantity": 0.006853341320848869,
      "child_quantity": 0.006884292043256994
    },
    {
      "entry_timestamp_ms": 1723989600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 52.00440079692505,
      "child_pnl": 52.239260509539946,
      "parent_quantity": 0.03630066252110021,
      "child_quantity": 0.036464601784639235
    },
    {
      "entry_timestamp_ms": 1724691600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.561679688935424,
      "child_pnl": -23.668087785859306,
      "parent_quantity": 0.028395918058639495,
      "child_quantity": 0.02852415830470503
    },
    {
      "entry_timestamp_ms": 1724457600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -14.063772164504828,
      "child_pnl": -14.127286279430123,
      "parent_quantity": 0.009972435078845307,
      "child_quantity": 0.010017472098805102
    },
    {
      "entry_timestamp_ms": 1724950800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 35.57317773313689,
      "child_pnl": 35.73383156571978,
      "parent_quantity": 0.022573256884806825,
      "child_quantity": 0.022675201115362427
    },
    {
      "entry_timestamp_ms": 1725336000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 61.81252533976144,
      "child_pnl": 62.09168002118901,
      "parent_quantity": 0.02701160254043078,
      "child_quantity": 0.02713359100895839
    },
    {
      "entry_timestamp_ms": 1725634800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 4.056551227032282,
      "child_pnl": 4.074871223816952,
      "parent_quantity": 0.010159489171332397,
      "child_quantity": 0.010205370955768497
    },
    {
      "entry_timestamp_ms": 1725652800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -7.354337770508502,
      "child_pnl": -7.3875510683984045,
      "parent_quantity": 0.004891644190812788,
      "child_quantity": 0.004913735593295333
    },
    {
      "entry_timestamp_ms": 1726682400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 82.74063372479476,
      "child_pnl": 83.11430289817987,
      "parent_quantity": 0.023619591380826793,
      "child_quantity": 0.023726261015680254
    },
    {
      "entry_timestamp_ms": 1726761600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 3.4648790944020447,
      "child_pnl": 3.480527010653113,
      "parent_quantity": 0.0019095789021866833,
      "child_quantity": 0.0019182028483395236
    },
    {
      "entry_timestamp_ms": 1726776000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 5.807857390208451,
      "child_pnl": 5.834086549600153,
      "parent_quantity": 0.004859823357107942,
      "child_quantity": 0.004881771051909127
    },
    {
      "entry_timestamp_ms": 1727319600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 36.348727790671234,
      "child_pnl": 36.51288412421252,
      "parent_quantity": 0.027430550527053642,
      "child_quantity": 0.02755443102783682
    },
    {
      "entry_timestamp_ms": 1727697600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.047356503775898,
      "child_pnl": -24.155957990401593,
      "parent_quantity": 0.0312596255750649,
      "child_quantity": 0.03140079875592083
    },
    {
      "entry_timestamp_ms": 1728892800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 58.13860108933895,
      "child_pnl": 58.4011637750815,
      "parent_quantity": 0.016238503433750363,
      "child_quantity": 0.0163118389628845
    },
    {
      "entry_timestamp_ms": 1728907200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 47.52756561731116,
      "child_pnl": 47.74220726746218,
      "parent_quantity": 0.01578073753860976,
      "child_quantity": 0.015852005727962453
    },
    {
      "entry_timestamp_ms": 1729562400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -8.200508124720223,
      "child_pnl": -8.237542855472896,
      "parent_quantity": 0.021143033855063928,
      "child_quantity": 0.02123851898283992
    },
    {
      "entry_timestamp_ms": 1729713600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 3.6740849081086657,
      "child_pnl": 3.6906776293479866,
      "parent_quantity": 0.008635351858111935,
      "child_quantity": 0.008674350408708542
    },
    {
      "entry_timestamp_ms": 1730232000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -25.653322928986437,
      "child_pnl": -25.7691772020555,
      "parent_quantity": 0.01194623327972367,
      "child_quantity": 0.012000184269868963
    },
    {
      "entry_timestamp_ms": 1730246400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -25.58563173186556,
      "child_pnl": -25.701180301285344,
      "parent_quantity": 0.011682589032754754,
      "child_quantity": 0.011735349365741677
    },
    {
      "entry_timestamp_ms": 1730188800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -9.16560503864988,
      "child_pnl": -9.206998292534783,
      "parent_quantity": 0.014584518824767601,
      "child_quantity": 0.014650384710102722
    },
    {
      "entry_timestamp_ms": 1730412000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.31480562443734,
      "child_pnl": -24.42461495160452,
      "parent_quantity": 0.024748019746484877,
      "child_quantity": 0.024859785533925528
    },
    {
      "entry_timestamp_ms": 1731225600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 69.53470175862267,
      "child_pnl": 69.8487309527204,
      "parent_quantity": 0.006227435817312102,
      "child_quantity": 0.006255559856123605
    },
    {
      "entry_timestamp_ms": 1731240000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 61.36659650119729,
      "child_pnl": 61.64373730077513,
      "parent_quantity": 0.005993507191654648,
      "child_quantity": 0.006020574773532654
    },
    {
      "entry_timestamp_ms": 1731888000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.17453062291037,
      "child_pnl": -11.224996487538853,
      "parent_quantity": 0.017219678759537487,
      "child_quantity": 0.017297445424335305
    },
    {
      "entry_timestamp_ms": 1731340800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 30.234683616564567,
      "child_pnl": 30.371228005046575,
      "parent_quantity": 0.003930207205309438,
      "child_quantity": 0.003947956613448193
    },
    {
      "entry_timestamp_ms": 1732291200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -4.206124316405044,
      "child_pnl": -4.225119807806454,
      "parent_quantity": 0.006944825982698683,
      "child_quantity": 0.00697618986362919
    },
    {
      "entry_timestamp_ms": 1732176000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.051862842129319,
      "child_pnl": -11.101774720570102,
      "parent_quantity": 0.00806722034818345,
      "child_quantity": 0.00810365313124683
    },
    {
      "entry_timestamp_ms": 1732190400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -19.253832860119807,
      "child_pnl": -19.34078607144362,
      "parent_quantity": 0.0079052737365316,
      "child_quantity": 0.007940975144286572
    },
    {
      "entry_timestamp_ms": 1733148000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.222149183979617,
      "child_pnl": -12.277346251937285,
      "parent_quantity": 0.010081368878102064,
      "child_quantity": 0.010126897859518877
    },
    {
      "entry_timestamp_ms": 1733371200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -13.10299879104762,
      "child_pnl": -13.162173908601144,
      "parent_quantity": 0.0032977972093911376,
      "child_quantity": 0.0033126905586652548
    },
    {
      "entry_timestamp_ms": 1733720400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.10644179599595,
      "child_pnl": -12.16111631194892,
      "parent_quantity": 0.009226602669387029,
      "child_quantity": 0.009268271397766491
    },
    {
      "entry_timestamp_ms": 1733752800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.125075166792833,
      "child_pnl": -12.179833833856927,
      "parent_quantity": 0.008927987217258062,
      "child_quantity": 0.008968307353245445
    },
    {
      "entry_timestamp_ms": 1733860800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 32.2254359654003,
      "child_pnl": 32.370970891555444,
      "parent_quantity": 0.0065679913670829045,
      "child_quantity": 0.006597653406089057
    },
    {
      "entry_timestamp_ms": 1734508800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.485581377116315,
      "child_pnl": -24.59616195332356,
      "parent_quantity": 0.016818884262858404,
      "child_quantity": 0.0168948408792975
    },
    {
      "entry_timestamp_ms": 1734321600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.052800478370512,
      "child_pnl": -10.098200440588021,
      "parent_quantity": 0.00463322018736998,
      "child_quantity": 0.0046541445081007635
    },
    {
      "entry_timestamp_ms": 1734580800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -25.237729248897505,
      "child_pnl": -25.35170663826485,
      "parent_quantity": 0.009212562828919036,
      "child_quantity": 0.009254168151262714
    },
    {
      "entry_timestamp_ms": 1734645600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.479276303793169,
      "child_pnl": -12.53563459658063,
      "parent_quantity": 0.006174380545880087,
      "child_quantity": 0.006202264979088779
    },
    {
      "entry_timestamp_ms": 1734703200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 5.840298831178172,
      "child_pnl": 5.86667450100718,
      "parent_quantity": 0.003932393021139983,
      "child_quantity": 0.003950152300752489
    },
    {
      "entry_timestamp_ms": 1735070400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -19.141520851031352,
      "child_pnl": -19.22796684439332,
      "parent_quantity": 0.01133846651557246,
      "child_quantity": 0.011389672739402223
    },
    {
      "entry_timestamp_ms": 1735164000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.917335790933734,
      "child_pnl": -24.025350084422204,
      "parent_quantity": 0.019699673049922276,
      "child_quantity": 0.01978863974274463
    },
    {
      "entry_timestamp_ms": 1735596000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -8.15163407539269,
      "child_pnl": -8.1884480835718,
      "parent_quantity": 0.00382840341226299,
      "child_quantity": 0.003845693059127468
    }
  ]
}
```

## 2024／成本2倍完整指標與減倉代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率、較早原版參考與原贏家被減少的對照：

```json
{
  "year": 2024,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -14.108928279772165,
    "average_win": 27.542726804478548,
    "cagr": 0.0032738836005485883,
    "exposure": 0.30096755833807626,
    "fees": 295.78563641601147,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.03876725683061577,
    "maximum_margin_ratio": 0.023278162960788665,
    "net_funding": -36.77957777573619,
    "number_of_trades": 101,
    "profit_factor": 1.0352304014589075,
    "sharpe_ratio": 0.12249455673764557,
    "slippage": 147.89333147271614,
    "sortino_ratio": 0.1761784776011605,
    "total_return": 0.0032806171691790453,
    "win_rate": 0.3465346534653465
  },
  "reference_original_metrics": {
    "average_loss": -14.30499429050049,
    "average_win": 26.74480952628108,
    "cagr": -0.0008044777363203082,
    "exposure": 0.30096755833807626,
    "fees": 280.4262319190377,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.042166618376891174,
    "maximum_margin_ratio": 0.02327816296078866,
    "net_funding": -36.523393642809474,
    "number_of_trades": 101,
    "profit_factor": 0.9914616705637282,
    "sharpe_ratio": -0.011737392674295263,
    "slippage": 140.21356506141274,
    "sortino_ratio": -0.016851289646115323,
    "total_return": -0.000806128975319953,
    "win_rate": 0.3465346534653465
  },
  "frequency": {
    "total": 101,
    "calendar_days": 366,
    "daily_average": 0.27595628415300544,
    "active_days": 85,
    "zero_entry_days": 281,
    "intraday": 59,
    "intraday_daily_average": 0.16120218579234974,
    "intraday_active_days": 54,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 39,
        "daily_average": 0.10655737704918032
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 20,
        "daily_average": 0.0546448087431694
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 34,
        "daily_average": 0.09289617486338798
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 8,
        "daily_average": 0.02185792349726776
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -201.74328001660416
    },
    "intraday/-1/stop_loss": {
      "count": 4,
      "pnl": -82.65913437529598
    },
    "swing/-1/stop_loss": {
      "count": 6,
      "pnl": -84.01443344958592
    },
    "intraday/1/time_limit": {
      "count": 12,
      "pnl": 181.1523590464012
    },
    "swing/1/signal": {
      "count": 11,
      "pnl": -39.67986205958084
    },
    "swing/1/time_limit": {
      "count": 11,
      "pnl": 539.8155016687775
    },
    "intraday/1/stop_loss": {
      "count": 19,
      "pnl": -324.71773706285035
    },
    "intraday/1/signal": {
      "count": 8,
      "pnl": -17.11262849590123
    },
    "intraday/-1/signal": {
      "count": 9,
      "pnl": -63.50280106699657
    },
    "intraday/-1/time_limit": {
      "count": 7,
      "pnl": 136.40437598536468
    },
    "swing/-1/signal": {
      "count": 2,
      "pnl": -11.136188481941875
    }
  },
  "exact_entry_exit_and_unit_pnl_matches": 101,
  "past_only_brake_trace_checks": 101,
  "parent_price_pnl_before_fees_funding": 339.1037198167663,
  "child_price_pnl_before_fees_funding": 365.371385883534,
  "parent_fees": 306.93287016546947,
  "child_fees": 295.78563641601147,
  "extra_guard_count": 5,
  "protected_parent_winners": 1,
  "parent_pnl_in_guard_cohort": -74.44075893966007,
  "child_pnl_in_guard_cohort": -37.255913915278626,
  "common_events": [
    {
      "entry_timestamp_ms": 1704744000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.483508220879553,
      "child_pnl": -24.483508220879553,
      "parent_quantity": 0.013709875954589435,
      "child_quantity": 0.013709875954589435
    },
    {
      "entry_timestamp_ms": 1706061600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.49702112670379,
      "child_pnl": -23.49702112670379,
      "parent_quantity": 0.03264226689101208,
      "child_quantity": 0.03264226689101208
    },
    {
      "entry_timestamp_ms": 1705968000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.393085151960275,
      "child_pnl": -23.393085151960275,
      "parent_quantity": 0.019465287635838643,
      "child_quantity": 0.019465287635838643
    },
    {
      "entry_timestamp_ms": 1706486400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 34.67009803555131,
      "child_pnl": 34.67009803555131,
      "parent_quantity": 0.034738135647209414,
      "child_quantity": 0.034738135647209414
    },
    {
      "entry_timestamp_ms": 1706572800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.195555155674795,
      "child_pnl": -12.195555155674795,
      "parent_quantity": 0.009737093071237192,
      "child_quantity": 0.009737093071237192
    },
    {
      "entry_timestamp_ms": 1706443200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -7.4367912106032,
      "child_pnl": -7.4367912106032,
      "parent_quantity": 0.009877629522104019,
      "child_quantity": 0.009877629522104019
    },
    {
      "entry_timestamp_ms": 1707177600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 4.333265599998563,
      "child_pnl": 4.333265599998563,
      "parent_quantity": 0.036587253668728024,
      "child_quantity": 0.036587253668728024
    },
    {
      "entry_timestamp_ms": 1707350400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 72.77308405799236,
      "child_pnl": 72.77308405799236,
      "parent_quantity": 0.010228142847449778,
      "child_quantity": 0.010228142847449778
    },
    {
      "entry_timestamp_ms": 1707364800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 75.60407299893645,
      "child_pnl": 75.60407299893645,
      "parent_quantity": 0.01011787962240219,
      "child_quantity": 0.01011787962240219
    },
    {
      "entry_timestamp_ms": 1707465600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 45.252157275955426,
      "child_pnl": 45.252157275955426,
      "parent_quantity": 0.00869664434556887,
      "child_quantity": 0.00869664434556887
    },
    {
      "entry_timestamp_ms": 1708398000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.19316924795533,
      "child_pnl": -24.19316924795533,
      "parent_quantity": 0.03254954447196391,
      "child_quantity": 0.03254954447196391
    },
    {
      "entry_timestamp_ms": 1708455600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -1.603206760031705,
      "child_pnl": -1.603206760031705,
      "parent_quantity": 0.022878588083796385,
      "child_quantity": 0.022878588083796385
    },
    {
      "entry_timestamp_ms": 1709020800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 108.94097961361538,
      "child_pnl": 108.94097961361538,
      "parent_quantity": 0.011991691458754759,
      "child_quantity": 0.011991691458754759
    },
    {
      "entry_timestamp_ms": 1709121600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 13.169612002431904,
      "child_pnl": 13.169612002431904,
      "parent_quantity": 0.009085278874257769,
      "child_quantity": 0.009085278874257769
    },
    {
      "entry_timestamp_ms": 1710158400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -26.366829146398295,
      "child_pnl": -26.366829146398295,
      "parent_quantity": 0.010238643960012709,
      "child_quantity": 0.010238643960012709
    },
    {
      "entry_timestamp_ms": 1710172800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -25.86352318688376,
      "child_pnl": -25.86352318688376,
      "parent_quantity": 0.009708950144211739,
      "child_quantity": 0.009708950144211739
    },
    {
      "entry_timestamp_ms": 1710270000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 4.4807671364863815,
      "child_pnl": 4.4807671364863815,
      "parent_quantity": 0.003779895529960078,
      "child_quantity": 0.003779895529960078
    },
    {
      "entry_timestamp_ms": 1710450000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -25.066335473915913,
      "child_pnl": -25.066335473915913,
      "parent_quantity": 0.00943564741181427,
      "child_quantity": 0.00943564741181427
    },
    {
      "entry_timestamp_ms": 1711220400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -5.659450407330381,
      "child_pnl": -5.659450407330381,
      "parent_quantity": 0.02356069222693687,
      "child_quantity": 0.02356069222693687
    },
    {
      "entry_timestamp_ms": 1711404000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.814166398622833,
      "child_pnl": -6.814166398622833,
      "parent_quantity": 0.006989038437559106,
      "child_quantity": 0.006989038437559106
    },
    {
      "entry_timestamp_ms": 1712260800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -0.39761229707456297,
      "child_pnl": -0.39761229707456297,
      "parent_quantity": 0.00955879837000164,
      "child_quantity": 0.00955879837000164
    },
    {
      "entry_timestamp_ms": 1712577600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.519126818722054,
      "child_pnl": -12.519126818722054,
      "parent_quantity": 0.005302823667453058,
      "child_quantity": 0.005302823667453058
    },
    {
      "entry_timestamp_ms": 1713830400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.32604357654763,
      "child_pnl": -12.32604357654763,
      "parent_quantity": 0.005846252760147899,
      "child_quantity": 0.005846252760147899
    },
    {
      "entry_timestamp_ms": 1713996000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.07190449438415,
      "child_pnl": -12.07190449438415,
      "parent_quantity": 0.010248430806974808,
      "child_quantity": 0.010248430806974808
    },
    {
      "entry_timestamp_ms": 1714154400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.00386086609705,
      "child_pnl": -12.00386086609705,
      "parent_quantity": 0.011102306237198248,
      "child_quantity": 0.011102306237198248
    },
    {
      "entry_timestamp_ms": 1714280400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 11.798208263386696,
      "child_pnl": 11.798208263386696,
      "parent_quantity": 0.012818374742961623,
      "child_quantity": 0.012818374742961623
    },
    {
      "entry_timestamp_ms": 1714507200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -3.615794198942827,
      "child_pnl": -3.615794198942827,
      "parent_quantity": 0.004850694904247635,
      "child_quantity": 0.004850694904247635
    },
    {
      "entry_timestamp_ms": 1715216400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": -23.702134806791534,
      "child_pnl": -11.851067403395767,
      "parent_quantity": 0.02654317727319598,
      "child_quantity": 0.01327158863659799
    },
    {
      "entry_timestamp_ms": 1715259600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": 20.932065103155633,
      "child_pnl": 10.478327947582905,
      "parent_quantity": 0.018565116609378672,
      "child_quantity": 0.009293463366347994
    },
    {
      "entry_timestamp_ms": 1715817600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -3.104509685743058,
      "child_pnl": -3.104938821625538,
      "parent_quantity": 0.005228946547198786,
      "child_quantity": 0.005229669343652371
    },
    {
      "entry_timestamp_ms": 1716249600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.330699238970421,
      "child_pnl": -12.332403709574534,
      "parent_quantity": 0.005278304803227012,
      "child_quantity": 0.0052790344224645175
    },
    {
      "entry_timestamp_ms": 1716501600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 4.821269866382621,
      "child_pnl": 4.821936309753143,
      "parent_quantity": 0.010814793659198753,
      "child_quantity": 0.010816288586414508
    },
    {
      "entry_timestamp_ms": 1716926400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -13.547469312140953,
      "child_pnl": -13.549341976679688,
      "parent_quantity": 0.015124611720742144,
      "child_quantity": 0.015126702393426394
    },
    {
      "entry_timestamp_ms": 1717426800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -14.090659235008008,
      "child_pnl": -14.092606984603808,
      "parent_quantity": 0.012363206967269799,
      "child_quantity": 0.012364915931412049
    },
    {
      "entry_timestamp_ms": 1718121600000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.054108804555357,
      "child_pnl": -12.055775042107495,
      "parent_quantity": 0.006755885539757667,
      "child_quantity": 0.0067568194047465105
    },
    {
      "entry_timestamp_ms": 1718107200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.94890523659039,
      "child_pnl": -11.950556931869977,
      "parent_quantity": 0.007350996854945768,
      "child_quantity": 0.007352012982077517
    },
    {
      "entry_timestamp_ms": 1719244800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.00506106436464,
      "child_pnl": -12.006720522055414,
      "parent_quantity": 0.008031570157918546,
      "child_quantity": 0.008032680360590244
    },
    {
      "entry_timestamp_ms": 1720090800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.028948326619354,
      "child_pnl": -12.030611086242608,
      "parent_quantity": 0.008866699236302759,
      "child_quantity": 0.008867924878734777
    },
    {
      "entry_timestamp_ms": 1720166400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -12.293310194175014,
      "child_pnl": -12.295009496497373,
      "parent_quantity": 0.0036291081612575323,
      "child_quantity": 0.003629609812304249
    },
    {
      "entry_timestamp_ms": 1720314000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 32.519577928074526,
      "child_pnl": 32.52407310418433,
      "parent_quantity": 0.012914344593558806,
      "child_quantity": 0.012916129741367893
    },
    {
      "entry_timestamp_ms": 1720436400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -13.668585012200086,
      "child_pnl": -13.670474418542861,
      "parent_quantity": 0.013934653342144632,
      "child_quantity": 0.01393657952707054
    },
    {
      "entry_timestamp_ms": 1720512000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.69058650337776,
      "child_pnl": -23.69386124940037,
      "parent_quantity": 0.024018400898328303,
      "child_quantity": 0.024021720958082842
    },
    {
      "entry_timestamp_ms": 1721088000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.237132163215593,
      "child_pnl": -12.238823700057617,
      "parent_quantity": 0.005127335864734276,
      "child_quantity": 0.0051280446155593015
    },
    {
      "entry_timestamp_ms": 1721102400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -0.5663639196219228,
      "child_pnl": -0.5664422080168532,
      "parent_quantity": 0.00023559194159880232,
      "child_quantity": 0.00023562450743558555
    },
    {
      "entry_timestamp_ms": 1720958400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 19.699520931628104,
      "child_pnl": 19.70224399328844,
      "parent_quantity": 0.006494836429801553,
      "child_quantity": 0.006495734210013242
    },
    {
      "entry_timestamp_ms": 1721016000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 2.916789464701433,
      "child_pnl": 2.9171926520474694,
      "parent_quantity": 0.005892692219512797,
      "child_quantity": 0.0058935067654256055
    },
    {
      "entry_timestamp_ms": 1721030400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 1.7649750634964505,
      "child_pnl": 1.765219035720118,
      "parent_quantity": 0.0059307172803289045,
      "child_quantity": 0.005931537082439852
    },
    {
      "entry_timestamp_ms": 1721336400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 32.78169838388005,
      "child_pnl": 32.78622979285894,
      "parent_quantity": 0.012145182260617974,
      "child_quantity": 0.012146861087239511
    },
    {
      "entry_timestamp_ms": 1721592000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -8.878625760301198,
      "child_pnl": -8.879853051334727,
      "parent_quantity": 0.011916318299235668,
      "child_quantity": 0.011917965490028047
    },
    {
      "entry_timestamp_ms": 1721725200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.587766588362747,
      "child_pnl": -23.591027121604775,
      "parent_quantity": 0.02262555194359862,
      "child_quantity": 0.0226286794700626
    },
    {
      "entry_timestamp_ms": 1721919600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 13.400698612271649,
      "child_pnl": 13.402550988719755,
      "parent_quantity": 0.008102357102115801,
      "child_quantity": 0.008103477089655585
    },
    {
      "entry_timestamp_ms": 1722027600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -23.685969498508115,
      "child_pnl": -11.844621803161436,
      "parent_quantity": 0.02065147157759496,
      "child_quantity": 0.010327163113621205
    },
    {
      "entry_timestamp_ms": 1722117600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.697818389088779,
      "child_pnl": -11.71328140343668,
      "parent_quantity": 0.009336349798055513,
      "child_quantity": 0.009348691254050336
    },
    {
      "entry_timestamp_ms": 1722279600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.948403546500046,
      "child_pnl": -11.96419780226028,
      "parent_quantity": 0.008369949466406082,
      "child_quantity": 0.00838101346521213
    },
    {
      "entry_timestamp_ms": 1722376800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.99552482878186,
      "child_pnl": -12.01138137282867,
      "parent_quantity": 0.008481736602572587,
      "child_quantity": 0.008492948369623363
    },
    {
      "entry_timestamp_ms": 1722844800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -24.594062416633964,
      "child_pnl": -12.31328630509539,
      "parent_quantity": 0.00594965371502923,
      "child_quantity": 0.002978759196763718
    },
    {
      "entry_timestamp_ms": 1723032000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -2.590597062448418,
      "child_pnl": -2.597228470253322,
      "parent_quantity": 0.01070187440033637,
      "child_quantity": 0.010729269047869252
    },
    {
      "entry_timestamp_ms": 1723165200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 1.956467614583402,
      "child_pnl": 1.9614757784532124,
      "parent_quantity": 0.006268025456470604,
      "child_quantity": 0.006284070341850848
    },
    {
      "entry_timestamp_ms": 1723255200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -14.158149045825612,
      "child_pnl": -14.1943910617865,
      "parent_quantity": 0.01719449550591017,
      "child_quantity": 0.017238509958544312
    },
    {
      "entry_timestamp_ms": 1723712400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": -23.3906573208821,
      "child_pnl": -11.725266351208933,
      "parent_quantity": 0.023177739087576164,
      "child_quantity": 0.011618534720614176
    },
    {
      "entry_timestamp_ms": 1723759200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 0.7161150356780212,
      "child_pnl": 0.7187955630162586,
      "parent_quantity": 0.006154967702929652,
      "child_quantity": 0.006178006681825061
    },
    {
      "entry_timestamp_ms": 1723989600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 35.522893624841416,
      "child_pnl": 35.65586121070495,
      "parent_quantity": 0.028290486023260307,
      "child_quantity": 0.028396381609052012
    },
    {
      "entry_timestamp_ms": 1724691600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.387746936607765,
      "child_pnl": -23.475290825396524,
      "parent_quantity": 0.022933382070109868,
      "child_quantity": 0.023019225202196833
    },
    {
      "entry_timestamp_ms": 1724457600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -14.555112602075635,
      "child_pnl": -14.609594599097314,
      "parent_quantity": 0.009094058193847733,
      "child_quantity": 0.009128098634823884
    },
    {
      "entry_timestamp_ms": 1724950800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 26.580910317724122,
      "child_pnl": 26.68040670200886,
      "parent_quantity": 0.019017262315469904,
      "child_quantity": 0.019088446816556078
    },
    {
      "entry_timestamp_ms": 1725336000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 46.98454446042361,
      "child_pnl": 47.160414746098546,
      "parent_quantity": 0.0222171005675645,
      "child_quantity": 0.02230026254920247
    },
    {
      "entry_timestamp_ms": 1725634800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 2.196721907881939,
      "child_pnl": 2.2049445716094334,
      "parent_quantity": 0.009308012666512116,
      "child_quantity": 0.009342853971573703
    },
    {
      "entry_timestamp_ms": 1725652800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -7.492349281739839,
      "child_pnl": -7.520394282999049,
      "parent_quantity": 0.004497253322254217,
      "child_quantity": 0.0045140872244580285
    },
    {
      "entry_timestamp_ms": 1726682400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 65.69758370818424,
      "child_pnl": 65.94349974179917,
      "parent_quantity": 0.01980289797857057,
      "child_quantity": 0.019877023233261855
    },
    {
      "entry_timestamp_ms": 1726761600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 7.27324516411284,
      "child_pnl": 7.300470025383419,
      "parent_quantity": 0.004484170025755965,
      "child_quantity": 0.004500954955193964
    },
    {
      "entry_timestamp_ms": 1726776000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 4.443806679608376,
      "child_pnl": 4.460440522911579,
      "parent_quantity": 0.004429555938952201,
      "child_quantity": 0.0044461364395688005
    },
    {
      "entry_timestamp_ms": 1727319600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 25.231336340322876,
      "child_pnl": 25.325781064244165,
      "parent_quantity": 0.022272268923381165,
      "child_quantity": 0.02235563740855362
    },
    {
      "entry_timestamp_ms": 1727697600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.77017097173123,
      "child_pnl": -23.85914633176395,
      "parent_quantity": 0.024765653281050112,
      "child_quantity": 0.024858354882555105
    },
    {
      "entry_timestamp_ms": 1728892800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 47.74605113477427,
      "child_pnl": 47.924771855584794,
      "parent_quantity": 0.014123456862715303,
      "child_quantity": 0.014176323106747001
    },
    {
      "entry_timestamp_ms": 1728907200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 38.69063357013976,
      "child_pnl": 38.83545848771781,
      "parent_quantity": 0.013758992970311251,
      "child_quantity": 0.013810494970640866
    },
    {
      "entry_timestamp_ms": 1729562400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.438979276978115,
      "child_pnl": -10.478053961827792,
      "parent_quantity": 0.01768987279740234,
      "child_quantity": 0.017756088677925618
    },
    {
      "entry_timestamp_ms": 1729713600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 1.6722565727133285,
      "child_pnl": 1.6785160830383155,
      "parent_quantity": 0.007428406431451159,
      "child_quantity": 0.0074562120849104374
    },
    {
      "entry_timestamp_ms": 1730232000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.985096698886935,
      "child_pnl": -25.078619710432772,
      "parent_quantity": 0.010577222662259755,
      "child_quantity": 0.010616814813096197
    },
    {
      "entry_timestamp_ms": 1730246400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.921431149771404,
      "child_pnl": -25.014715851497726,
      "parent_quantity": 0.010360756790261893,
      "child_quantity": 0.010399538676463779
    },
    {
      "entry_timestamp_ms": 1730188800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.670987018259003,
      "child_pnl": -10.710930143320374,
      "parent_quantity": 0.012689776350794806,
      "child_quantity": 0.01273727611093071
    },
    {
      "entry_timestamp_ms": 1730412000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.904797223639843,
      "child_pnl": -23.994276510179766,
      "parent_quantity": 0.020041599601660406,
      "child_quantity": 0.020116618352779614
    },
    {
      "entry_timestamp_ms": 1731225600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 59.38985997303703,
      "child_pnl": 59.612165238728124,
      "parent_quantity": 0.005442771577160529,
      "child_quantity": 0.005463144697792669
    },
    {
      "entry_timestamp_ms": 1731240000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 52.42209370772925,
      "child_pnl": 52.61831756606249,
      "parent_quantity": 0.005251211460031155,
      "child_quantity": 0.0052708675420517605
    },
    {
      "entry_timestamp_ms": 1731888000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -13.052095162011172,
      "child_pnl": -13.100951136484483,
      "parent_quantity": 0.014216100645717326,
      "child_quantity": 0.014269313669499031
    },
    {
      "entry_timestamp_ms": 1731340800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 26.394784339409583,
      "child_pnl": 26.493584025889646,
      "parent_quantity": 0.003553356292713367,
      "child_quantity": 0.0035666570449816052
    },
    {
      "entry_timestamp_ms": 1732291200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -5.256190867045434,
      "child_pnl": -5.2758655877427385,
      "parent_quantity": 0.00583157433322456,
      "child_quantity": 0.005853402801621914
    },
    {
      "entry_timestamp_ms": 1732176000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.939940663168256,
      "child_pnl": -11.984633674444364,
      "parent_quantity": 0.007195433606293862,
      "child_quantity": 0.007222367207085914
    },
    {
      "entry_timestamp_ms": 1732190400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -19.237841328117742,
      "child_pnl": -19.30985148994859,
      "parent_quantity": 0.007055688945443811,
      "child_quantity": 0.007082099460746634
    },
    {
      "entry_timestamp_ms": 1733148000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.006028140549983,
      "child_pnl": -12.05096852729094,
      "parent_quantity": 0.008013636291770725,
      "child_quantity": 0.008043632549478735
    },
    {
      "entry_timestamp_ms": 1733371200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.710112849180625,
      "child_pnl": -12.757688731918577,
      "parent_quantity": 0.002971599334258743,
      "child_quantity": 0.0029827224818773724
    },
    {
      "entry_timestamp_ms": 1733720400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.902128475808006,
      "child_pnl": -11.946679950324107,
      "parent_quantity": 0.007396540897472844,
      "child_quantity": 0.00742422727339887
    },
    {
      "entry_timestamp_ms": 1733752800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.90988801918001,
      "child_pnl": -11.954468538845433,
      "parent_quantity": 0.0072019831455864556,
      "child_quantity": 0.007228941262298788
    },
    {
      "entry_timestamp_ms": 1733860800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 25.683517066081265,
      "child_pnl": 25.779654371133823,
      "parent_quantity": 0.005570042452518144,
      "child_quantity": 0.005590891967365961
    },
    {
      "entry_timestamp_ms": 1734508800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.999965186916906,
      "child_pnl": -24.089800701596946,
      "parent_quantity": 0.013584330696623027,
      "child_quantity": 0.013635178909535446
    },
    {
      "entry_timestamp_ms": 1734321600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.03980927312793,
      "child_pnl": -10.07738980402939,
      "parent_quantity": 0.004047106633662456,
      "child_quantity": 0.004062255568445006
    },
    {
      "entry_timestamp_ms": 1734580800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.543069629601586,
      "child_pnl": -24.634938066694367,
      "parent_quantity": 0.008075090600507432,
      "child_quantity": 0.008105316891026386
    },
    {
      "entry_timestamp_ms": 1734645600000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -12.157837757670999,
      "child_pnl": -12.203346390864855,
      "parent_quantity": 0.005261419610860728,
      "child_quantity": 0.005281113903540243
    },
    {
      "entry_timestamp_ms": 1734703200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 4.205121385856605,
      "child_pnl": 4.220861793855047,
      "parent_quantity": 0.003513181504304892,
      "child_quantity": 0.003526331876238584
    },
    {
      "entry_timestamp_ms": 1735070400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -19.303806739089367,
      "child_pnl": -19.376063819471945,
      "parent_quantity": 0.009734624426795305,
      "child_quantity": 0.00977106260446711
    },
    {
      "entry_timestamp_ms": 1735164000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.535533121108106,
      "child_pnl": -23.623630196030387,
      "parent_quantity": 0.015577190916666366,
      "child_quantity": 0.01563549870804728
    },
    {
      "entry_timestamp_ms": 1735596000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -8.250931112132065,
      "child_pnl": -8.281815600391742,
      "parent_quantity": 0.0034262344132502515,
      "child_quantity": 0.003439059329017072
    }
  ]
}
```

## 2025／成本1倍完整指標與減倉代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率、較早原版參考與原贏家被減少的對照：

```json
{
  "year": 2025,
  "cost": 1,
  "checks": "passed",
  "metrics": {
    "average_loss": -13.406290120462481,
    "average_win": 20.983959218927943,
    "cagr": -0.024555417084932474,
    "exposure": 0.24574820226001598,
    "fees": 141.0222809076097,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04380546098900817,
    "maximum_margin_ratio": 0.0226569834142028,
    "net_funding": -5.190003244101842,
    "number_of_trades": 85,
    "profit_factor": 0.6897634159985696,
    "sharpe_ratio": -0.9964000497629618,
    "slippage": 70.51113328760712,
    "sortino_ratio": -1.4050158745206902,
    "total_return": -0.02453881774151412,
    "win_rate": 0.3058823529411765
  },
  "reference_original_metrics": {
    "average_loss": -13.098555618676043,
    "average_win": 18.172209899246887,
    "cagr": -0.030053991197581342,
    "exposure": 0.2444926378267321,
    "fees": 128.31101384885662,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.042921371143793574,
    "maximum_margin_ratio": 0.0226569834142028,
    "net_funding": -5.291518159530415,
    "number_of_trades": 85,
    "profit_factor": 0.6113721795825482,
    "sharpe_ratio": -1.2692918904961452,
    "slippage": 64.15548127959347,
    "sortino_ratio": -1.7426998533306284,
    "total_return": -0.030033732412145353,
    "win_rate": 0.3058823529411765
  },
  "frequency": {
    "total": 85,
    "calendar_days": 365,
    "daily_average": 0.2328767123287671,
    "active_days": 74,
    "zero_entry_days": 291,
    "intraday": 43,
    "intraday_daily_average": 0.1178082191780822,
    "intraday_active_days": 43,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 15,
        "daily_average": 0.0410958904109589
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 28,
        "daily_average": 0.07671232876712329
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 23,
        "daily_average": 0.06301369863013699
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -180.35354836338684
    },
    "intraday/1/stop_loss": {
      "count": 6,
      "pnl": -115.43198897290242
    },
    "intraday/-1/signal": {
      "count": 5,
      "pnl": 6.780190084447494
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 58.13177455270185
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 11.687214182198982
    },
    "intraday/-1/stop_loss": {
      "count": 13,
      "pnl": -216.70132710516407
    },
    "intraday/1/signal": {
      "count": 5,
      "pnl": -28.767205162392106
    },
    "intraday/-1/time_limit": {
      "count": 10,
      "pnl": 246.93674600459485
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 23.140538962314828
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -153.1938574472897
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 65.13971049493409
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 37.24357535478321
    }
  },
  "exact_entry_exit_and_unit_pnl_matches": 85,
  "past_only_brake_trace_checks": 85,
  "parent_price_pnl_before_fees_funding": -121.62486426311216,
  "child_price_pnl_before_fees_funding": -99.17589326344834,
  "parent_fees": 151.10226416965372,
  "child_fees": 141.0222809076097,
  "extra_guard_count": 10,
  "protected_parent_winners": 4,
  "parent_pnl_in_guard_cohort": -64.098709677816,
  "child_pnl_in_guard_cohort": -31.972614485467304,
  "common_events": [
    {
      "entry_timestamp_ms": 1736150400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.19673620982446,
      "child_pnl": -24.19673620982446,
      "parent_quantity": 0.013404767030289923,
      "child_quantity": 0.013404767030289923
    },
    {
      "entry_timestamp_ms": 1736326800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -22.70615687998392,
      "child_pnl": -22.70615687998392,
      "parent_quantity": 0.023274050831663243,
      "child_quantity": 0.023274050831663243
    },
    {
      "entry_timestamp_ms": 1736438400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.05155131058018,
      "child_pnl": -24.05155131058018,
      "parent_quantity": 0.008819737636681486,
      "child_quantity": 0.008819737636681486
    },
    {
      "entry_timestamp_ms": 1736733600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 2.0940449817480125,
      "child_pnl": 2.0940449817480125,
      "parent_quantity": 0.005807553544417902,
      "child_quantity": 0.005807553544417902
    },
    {
      "entry_timestamp_ms": 1737129600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.58120160057521,
      "child_pnl": -24.58120160057521,
      "parent_quantity": 0.007049369864914535,
      "child_quantity": 0.007049369864914535
    },
    {
      "entry_timestamp_ms": 1737100800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -3.4968602307058805,
      "child_pnl": -3.4968602307058805,
      "parent_quantity": 0.007403103444974931,
      "child_quantity": 0.007403103444974931
    },
    {
      "entry_timestamp_ms": 1737428400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": 23.24170420253265,
      "child_pnl": 11.620852101266324,
      "parent_quantity": 0.008670579281248985,
      "child_quantity": 0.004335289640624493
    },
    {
      "entry_timestamp_ms": 1737568800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.243246264391647,
      "child_pnl": -23.21603509417241,
      "parent_quantity": 0.016486431933724333,
      "child_quantity": 0.016467131053780393
    },
    {
      "entry_timestamp_ms": 1738029600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.461223360149397,
      "child_pnl": -23.433757001313683,
      "parent_quantity": 0.012801806254417899,
      "child_quantity": 0.012786819013602213
    },
    {
      "entry_timestamp_ms": 1738476000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -7.071855615936016,
      "child_pnl": -7.063576502737188,
      "parent_quantity": 0.007613446085194893,
      "child_quantity": 0.007604532925001058
    },
    {
      "entry_timestamp_ms": 1738627200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 25.918813649066717,
      "child_pnl": 25.888470157367532,
      "parent_quantity": 0.007863958968777875,
      "child_quantity": 0.007854752529898276
    },
    {
      "entry_timestamp_ms": 1740427200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 38.90766672132805,
      "child_pnl": 38.862117010674694,
      "parent_quantity": 0.0061695392859384204,
      "child_quantity": 0.006162316526183851
    },
    {
      "entry_timestamp_ms": 1740484800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 5.537360363737654,
      "child_pnl": 5.530877704056257,
      "parent_quantity": 0.0035288454388683276,
      "child_quantity": 0.0035247141736903845
    },
    {
      "entry_timestamp_ms": 1741564800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -24.250937294496993,
      "child_pnl": -24.22254640730377,
      "parent_quantity": 0.007415821684042988,
      "child_quantity": 0.0074071398853017695
    },
    {
      "entry_timestamp_ms": 1741698000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.061310904121523,
      "child_pnl": -23.03431272799101,
      "parent_quantity": 0.020873835630373667,
      "child_quantity": 0.02084939835995087
    },
    {
      "entry_timestamp_ms": 1741651200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -24.268949712598594,
      "child_pnl": -24.24053773803361,
      "parent_quantity": 0.005979010523718958,
      "child_quantity": 0.005972010818460369
    },
    {
      "entry_timestamp_ms": 1741748400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.398761458056594,
      "child_pnl": -23.371368224180745,
      "parent_quantity": 0.014682861754197493,
      "child_quantity": 0.014665672337282392
    },
    {
      "entry_timestamp_ms": 1742284800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.489670696530517,
      "child_pnl": -11.476219589850757,
      "parent_quantity": 0.009862386250615663,
      "child_quantity": 0.0098508402269673
    },
    {
      "entry_timestamp_ms": 1742428800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.933124387373569,
      "child_pnl": -11.919154123699617,
      "parent_quantity": 0.004383021297764159,
      "child_quantity": 0.004377890037816588
    },
    {
      "entry_timestamp_ms": 1742569200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -4.211514968599557,
      "child_pnl": -4.206584493338578,
      "parent_quantity": 0.008689773003043737,
      "child_quantity": 0.00867959977295089
    },
    {
      "entry_timestamp_ms": 1742817600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.599594607735504,
      "child_pnl": -11.58601481170551,
      "parent_quantity": 0.007507798818544298,
      "child_quantity": 0.007499009340977379
    },
    {
      "entry_timestamp_ms": 1743022800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -4.257393032125665,
      "child_pnl": -4.252408846819979,
      "parent_quantity": 0.006887133355372255,
      "child_quantity": 0.006879070498922517
    },
    {
      "entry_timestamp_ms": 1742803200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.546651915594788,
      "child_pnl": -11.533134100261956,
      "parent_quantity": 0.008043167021510039,
      "child_quantity": 0.008033750781436061
    },
    {
      "entry_timestamp_ms": 1743440400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -5.204345722551676,
      "child_pnl": -5.198252927434967,
      "parent_quantity": 0.012503295838377683,
      "child_quantity": 0.012488658067582262
    },
    {
      "entry_timestamp_ms": 1743555600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.183470791329261,
      "child_pnl": -11.170378156854575,
      "parent_quantity": 0.012021243073902755,
      "child_quantity": 0.01200716964853824
    },
    {
      "entry_timestamp_ms": 1743764400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.4115573711275715,
      "child_pnl": -6.4040512776580245,
      "parent_quantity": 0.004917698827056961,
      "child_quantity": 0.004911941613182966
    },
    {
      "entry_timestamp_ms": 1743998400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.839003275283547,
      "child_pnl": -11.825143200417688,
      "parent_quantity": 0.004513058412736025,
      "child_quantity": 0.0045077749166494005
    },
    {
      "entry_timestamp_ms": 1744412400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.311639327796849,
      "child_pnl": -11.298396644752223,
      "parent_quantity": 0.009726636371989696,
      "child_quantity": 0.00971524927248697
    },
    {
      "entry_timestamp_ms": 1744772400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 1.1233936870565557,
      "child_pnl": 1.1220785154796593,
      "parent_quantity": 0.010765879483795406,
      "child_quantity": 0.010753275728886942
    },
    {
      "entry_timestamp_ms": 1745611200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -2.757430485237387,
      "child_pnl": -2.754202325562586,
      "parent_quantity": 0.0009850230023441642,
      "child_quantity": 0.0009838698231246178
    },
    {
      "entry_timestamp_ms": 1745222400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 49.53805157792879,
      "child_pnl": 49.480056737686446,
      "parent_quantity": 0.007106897731457062,
      "child_quantity": 0.007098577593998564
    },
    {
      "entry_timestamp_ms": 1745352000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 15.67800820503489,
      "child_pnl": 15.659653757247648,
      "parent_quantity": 0.004322573753336286,
      "child_quantity": 0.0043175132601138986
    },
    {
      "entry_timestamp_ms": 1746586800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -22.896611070257716,
      "child_pnl": -11.434902855180681,
      "parent_quantity": 0.01629047687341364,
      "child_quantity": 0.008135702700301659
    },
    {
      "entry_timestamp_ms": 1746684000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -18.498607104654692,
      "child_pnl": -9.249281271829911,
      "parent_quantity": 0.022866909222053963,
      "child_quantity": 0.01143342706916346
    },
    {
      "entry_timestamp_ms": 1746705600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 25.40096207200416,
      "child_pnl": 25.424950224407038,
      "parent_quantity": 0.009370111965132542,
      "child_quantity": 0.009378960908460536
    },
    {
      "entry_timestamp_ms": 1747324800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 3.1478952504860125,
      "child_pnl": 3.150868058791576,
      "parent_quantity": 0.005208988740017652,
      "child_quantity": 0.005213908003130845
    },
    {
      "entry_timestamp_ms": 1749513600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.41330769344579,
      "child_pnl": -23.435418745445077,
      "parent_quantity": 0.010877424018523551,
      "child_quantity": 0.010887696436724381
    },
    {
      "entry_timestamp_ms": 1750118400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": 18.313704675846935,
      "child_pnl": 9.165499883193212,
      "parent_quantity": 0.009470900026100794,
      "child_quantity": 0.004739922075812716
    },
    {
      "entry_timestamp_ms": 1750622400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -23.73130425455381,
      "child_pnl": -11.865751963840905,
      "parent_quantity": 0.007676761772365288,
      "child_quantity": 0.003838413181985259
    },
    {
      "entry_timestamp_ms": 1750694400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -22.83382544743526,
      "child_pnl": -22.861752781767027,
      "parent_quantity": 0.014944643896723404,
      "child_quantity": 0.014962922221024941
    },
    {
      "entry_timestamp_ms": 1752480000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.675498661538883,
      "child_pnl": -11.68977859703903,
      "parent_quantity": 0.0045976805486310215,
      "child_quantity": 0.00460330382722391
    },
    {
      "entry_timestamp_ms": 1752192000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 2.8293316452462256,
      "child_pnl": 2.8327921118672976,
      "parent_quantity": 0.0038825450072238225,
      "child_quantity": 0.003887293626009775
    },
    {
      "entry_timestamp_ms": 1752206400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -0.45623066348879704,
      "child_pnl": -0.45678866487586145,
      "parent_quantity": 0.003762361911499531,
      "child_quantity": 0.0037669635381179624
    },
    {
      "entry_timestamp_ms": 1753909200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 2.433956284403628,
      "child_pnl": 2.436933179845871,
      "parent_quantity": 0.012774747006758283,
      "child_quantity": 0.012790371398364617
    },
    {
      "entry_timestamp_ms": 1754092800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -9.638366995163631,
      "child_pnl": -4.825077689470639,
      "parent_quantity": 0.007279462807872724,
      "child_quantity": 0.0036441830450347655
    },
    {
      "entry_timestamp_ms": 1754884800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.653106697265038,
      "child_pnl": -11.673138291083886,
      "parent_quantity": 0.004641575840037521,
      "child_quantity": 0.004649554670432065
    },
    {
      "entry_timestamp_ms": 1755144000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.68613262414605,
      "child_pnl": -11.706220989259455,
      "parent_quantity": 0.004138053267785586,
      "child_quantity": 0.004145166547052179
    },
    {
      "entry_timestamp_ms": 1755129600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.757516858313524,
      "child_pnl": -11.777727932333747,
      "parent_quantity": 0.003941934445665857,
      "child_quantity": 0.003948710598302873
    },
    {
      "entry_timestamp_ms": 1755504000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.37315185115708,
      "child_pnl": -11.392702204916043,
      "parent_quantity": 0.006183318252737529,
      "child_quantity": 0.006193947325559852
    },
    {
      "entry_timestamp_ms": 1755716400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -22.27711380432507,
      "child_pnl": -22.315407978297515,
      "parent_quantity": 0.016909011100989295,
      "child_quantity": 0.016938077550911437
    },
    {
      "entry_timestamp_ms": 1755633600000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.422760144839598,
      "child_pnl": -11.442395774844197,
      "parent_quantity": 0.004170532232985989,
      "child_quantity": 0.004177701343324541
    },
    {
      "entry_timestamp_ms": 1755648000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.45530018105187,
      "child_pnl": -11.474991747108993,
      "parent_quantity": 0.004109343658258762,
      "child_quantity": 0.004116407585944557
    },
    {
      "entry_timestamp_ms": 1756256400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -22.156711192423966,
      "child_pnl": -11.097399197652287,
      "parent_quantity": 0.01639336174867912,
      "child_quantity": 0.008210770900819451
    },
    {
      "entry_timestamp_ms": 1756180800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.546021753145693,
      "child_pnl": -11.56586926883324,
      "parent_quantity": 0.0035070470382371115,
      "child_quantity": 0.003513075623025583
    },
    {
      "entry_timestamp_ms": 1756724400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.188111563734527,
      "child_pnl": -11.220271456910158,
      "parent_quantity": 0.0067275818045363115,
      "child_quantity": 0.006746920037886211
    },
    {
      "entry_timestamp_ms": 1757098800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -9.749022677532036,
      "child_pnl": -9.777045952603094,
      "parent_quantity": 0.008350710807031087,
      "child_quantity": 0.008374714676313658
    },
    {
      "entry_timestamp_ms": 1758916800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -4.334717464095395,
      "child_pnl": -4.347177480229282,
      "parent_quantity": 0.007617579126712027,
      "child_quantity": 0.007639475630833964
    },
    {
      "entry_timestamp_ms": 1758844800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -5.73975105572323,
      "child_pnl": -5.756249799032613,
      "parent_quantity": 0.004272355232591192,
      "child_quantity": 0.004284635990349621
    },
    {
      "entry_timestamp_ms": 1759334400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 17.308011040638203,
      "child_pnl": 17.3577624024278,
      "parent_quantity": 0.004477471257100672,
      "child_quantity": 0.004490341614757106
    },
    {
      "entry_timestamp_ms": 1759348800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 16.452284880662205,
      "child_pnl": 16.49957648311389,
      "parent_quantity": 0.004264386582693939,
      "child_quantity": 0.004276644434805782
    },
    {
      "entry_timestamp_ms": 1759377600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 11.19580925994854,
      "child_pnl": 11.227991279922481,
      "parent_quantity": 0.0044037955424048,
      "child_quantity": 0.004416454121415593
    },
    {
      "entry_timestamp_ms": 1759435200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 1.9488917323911905,
      "child_pnl": 1.9544937635800603,
      "parent_quantity": 0.004132019294475897,
      "child_quantity": 0.004143896660763589
    },
    {
      "entry_timestamp_ms": 1760277600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.073846022754816,
      "child_pnl": -11.103696946063236,
      "parent_quantity": 0.008594070895780839,
      "child_quantity": 0.008617237278146091
    },
    {
      "entry_timestamp_ms": 1760155200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -9.379778311773626,
      "child_pnl": -4.7033701024611965,
      "parent_quantity": 0.003961048878950252,
      "child_quantity": 0.0019862173979375477
    },
    {
      "entry_timestamp_ms": 1760328000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -9.743532812936873,
      "child_pnl": -9.776316208985953,
      "parent_quantity": 0.007503227549475639,
      "child_quantity": 0.007528473144181724
    },
    {
      "entry_timestamp_ms": 1760500800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 2.1543429513608525,
      "child_pnl": 2.161591521212871,
      "parent_quantity": 0.005854167360821751,
      "child_quantity": 0.005873864475904343
    },
    {
      "entry_timestamp_ms": 1760623200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 69.93107366592747,
      "child_pnl": 70.16636594934687,
      "parent_quantity": 0.01489283459201801,
      "child_quantity": 0.014942943490309538
    },
    {
      "entry_timestamp_ms": 1760644800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": 0.46687139726426075,
      "child_pnl": 0.23422112370403952,
      "parent_quantity": 0.005855593023646807,
      "child_quantity": 0.0029376474677796235
    },
    {
      "entry_timestamp_ms": 1760659200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": 0.18038897536759507,
      "child_pnl": 0.18259548680474053,
      "parent_quantity": 0.0031121112413319027,
      "child_quantity": 0.003150178473731636
    },
    {
      "entry_timestamp_ms": 1761069600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 28.813741567668632,
      "child_pnl": 28.909995510950314,
      "parent_quantity": 0.009938662184356621,
      "child_quantity": 0.00997186285091852
    },
    {
      "entry_timestamp_ms": 1761537600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.422576188036253,
      "child_pnl": -23.500820636596305,
      "parent_quantity": 0.011029317754524042,
      "child_quantity": 0.01106616181807915
    },
    {
      "entry_timestamp_ms": 1761494400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -13.168153849798417,
      "child_pnl": -13.212142817034982,
      "parent_quantity": 0.010929131004938468,
      "child_quantity": 0.010965640388955707
    },
    {
      "entry_timestamp_ms": 1761930000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -16.01602669276729,
      "child_pnl": -16.069529141286974,
      "parent_quantity": 0.008442388496055362,
      "child_quantity": 0.008470590775219729
    },
    {
      "entry_timestamp_ms": 1762286400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.718559714103739,
      "child_pnl": -11.757706229644437,
      "parent_quantity": 0.002906994429799275,
      "child_quantity": 0.0029167054101073677
    },
    {
      "entry_timestamp_ms": 1762376400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 56.15254615595677,
      "child_pnl": 56.340126931612886,
      "parent_quantity": 0.021398004277643646,
      "child_quantity": 0.02146948552853377
    },
    {
      "entry_timestamp_ms": 1762560000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 15.2381489119817,
      "child_pnl": 15.289052815511457,
      "parent_quantity": 0.020520219191191486,
      "child_quantity": 0.02058876815105212
    },
    {
      "entry_timestamp_ms": 1763622000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 94.43094470138934,
      "child_pnl": 94.7463966455243,
      "parent_quantity": 0.015350642517941904,
      "child_quantity": 0.015401922212763536
    },
    {
      "entry_timestamp_ms": 1763121600000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 37.11957530129138,
      "child_pnl": 37.24357535478321,
      "parent_quantity": 0.00270266365985892,
      "child_quantity": 0.0027116920616030876
    },
    {
      "entry_timestamp_ms": 1763712000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.363317746937905,
      "child_pnl": -6.384574771960451,
      "parent_quantity": 0.0025523080569560155,
      "child_quantity": 0.0025608341872530712
    },
    {
      "entry_timestamp_ms": 1764572400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -22.44523560943908,
      "child_pnl": -22.520215196183173,
      "parent_quantity": 0.025314417972377563,
      "child_quantity": 0.0253989822260688
    },
    {
      "entry_timestamp_ms": 1764748800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -22.81371046965074,
      "child_pnl": -22.889920967632523,
      "parent_quantity": 0.018340887349359004,
      "child_quantity": 0.01840215612719249
    },
    {
      "entry_timestamp_ms": 1764882000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.077442769075596,
      "child_pnl": -10.111107040077716,
      "parent_quantity": 0.006183659614493541,
      "child_quantity": 0.006204316481301653
    },
    {
      "entry_timestamp_ms": 1765429200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.423649550773014,
      "child_pnl": -11.46181090213197,
      "parent_quantity": 0.008565131327083267,
      "child_quantity": 0.00859374363565906
    },
    {
      "entry_timestamp_ms": 1765893600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.43157434199348,
      "child_pnl": -11.469762166568445,
      "parent_quantity": 0.00879087389011985,
      "child_quantity": 0.008820240304572787
    },
    {
      "entry_timestamp_ms": 1765828800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.328283454030224,
      "child_pnl": -23.40621291234684,
      "parent_quantity": 0.00962403541384731,
      "child_quantity": 0.009656185051779263
    }
  ]
}
```

## 2025／成本2倍完整指標與減倉代價

收益、CAGR、Sharpe、Sortino、回撤、勝率、PF、平均盈虧、交易數、曝險、費用、滑價、funding、頻率、較早原版參考與原贏家被減少的對照：

```json
{
  "year": 2025,
  "cost": 2,
  "checks": "passed",
  "metrics": {
    "average_loss": -12.374612417773704,
    "average_win": 18.99662252687067,
    "cagr": -0.036191807142951116,
    "exposure": 0.24574820226001598,
    "fees": 228.9865357405867,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04894833098661955,
    "maximum_margin_ratio": 0.02268118178613781,
    "net_funding": -4.141020893828069,
    "number_of_trades": 85,
    "profit_factor": 0.5360766847397604,
    "sharpe_ratio": -1.7261047799413975,
    "slippage": 114.49325381621057,
    "sortino_ratio": -2.3911596173516005,
    "total_return": -0.03616748867285968,
    "win_rate": 0.25882352941176473
  },
  "reference_original_metrics": {
    "average_loss": -12.152397018857757,
    "average_win": 16.921984957871288,
    "cagr": -0.039358136617469563,
    "exposure": 0.2444926378267321,
    "fees": 211.75470180319033,
    "liquidation_count": 0,
    "liquidation_fees": 0,
    "maximum_drawdown": -0.04713477804219368,
    "maximum_margin_ratio": 0.02268118178613781,
    "net_funding": -4.331547460663529,
    "number_of_trades": 85,
    "profit_factor": 0.48626329268975943,
    "sharpe_ratio": -1.9084155938081524,
    "slippage": 105.87727954777498,
    "sortino_ratio": -2.5839267405021014,
    "total_return": -0.03933173431148573,
    "win_rate": 0.25882352941176473
  },
  "frequency": {
    "total": 85,
    "calendar_days": 365,
    "daily_average": 0.2328767123287671,
    "active_days": 74,
    "zero_entry_days": 291,
    "intraday": 43,
    "intraday_daily_average": 0.1178082191780822,
    "intraday_active_days": 43,
    "groups": [
      {
        "sleeve": "intraday",
        "direction": 1,
        "count": 15,
        "daily_average": 0.0410958904109589
      },
      {
        "sleeve": "intraday",
        "direction": -1,
        "count": 28,
        "daily_average": 0.07671232876712329
      },
      {
        "sleeve": "swing",
        "direction": 1,
        "count": 23,
        "daily_average": 0.06301369863013699
      },
      {
        "sleeve": "swing",
        "direction": -1,
        "count": 19,
        "daily_average": 0.052054794520547946
      }
    ]
  },
  "grouped": {
    "swing/1/stop_loss": {
      "count": 12,
      "pnl": -177.74835040120502
    },
    "intraday/1/stop_loss": {
      "count": 6,
      "pnl": -105.13911920539839
    },
    "intraday/-1/signal": {
      "count": 5,
      "pnl": -3.886668364514488
    },
    "swing/1/signal": {
      "count": 9,
      "pnl": 43.30554908714467
    },
    "intraday/1/time_limit": {
      "count": 4,
      "pnl": 3.9038595858326044
    },
    "intraday/-1/stop_loss": {
      "count": 13,
      "pnl": -206.93500276347163
    },
    "intraday/1/signal": {
      "count": 5,
      "pnl": -35.281891132206496
    },
    "intraday/-1/time_limit": {
      "count": 10,
      "pnl": 172.8911521442212
    },
    "swing/-1/signal": {
      "count": 8,
      "pnl": 11.878646989672633
    },
    "swing/-1/stop_loss": {
      "count": 10,
      "pnl": -152.85870946807682
    },
    "swing/1/time_limit": {
      "count": 2,
      "pnl": 54.29907256825571
    },
    "swing/-1/time_limit": {
      "count": 1,
      "pnl": 33.89657423115739
    }
  },
  "exact_entry_exit_and_unit_pnl_matches": 85,
  "past_only_brake_trace_checks": 85,
  "parent_price_pnl_before_fees_funding": -134.81351122961016,
  "child_price_pnl_before_fees_funding": -128.54733009417387,
  "parent_fees": 241.63991377797672,
  "child_fees": 228.9865357405867,
  "extra_guard_count": 8,
  "protected_parent_winners": 2,
  "parent_pnl_in_guard_cohort": -37.93219159316473,
  "child_pnl_in_guard_cohort": -19.055415561847283,
  "common_events": [
    {
      "entry_timestamp_ms": 1736150400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.306086900156675,
      "child_pnl": -24.306086900156675,
      "parent_quantity": 0.011570351481377502,
      "child_quantity": 0.011570351481377502
    },
    {
      "entry_timestamp_ms": 1736326800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.176498822491226,
      "child_pnl": -23.176498822491226,
      "parent_quantity": 0.018360530297110354,
      "child_quantity": 0.018360530297110354
    },
    {
      "entry_timestamp_ms": 1736438400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.124560382280485,
      "child_pnl": -24.124560382280485,
      "parent_quantity": 0.008025652886791966,
      "child_quantity": 0.008025652886791966
    },
    {
      "entry_timestamp_ms": 1736733600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 0.4047426016243412,
      "child_pnl": 0.4047426016243412,
      "parent_quantity": 0.005123602694016991,
      "child_quantity": 0.005123602694016991
    },
    {
      "entry_timestamp_ms": 1737129600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -24.592213156650054,
      "child_pnl": -24.592213156650054,
      "parent_quantity": 0.006481570846140382,
      "child_quantity": 0.006481570846140382
    },
    {
      "entry_timestamp_ms": 1737100800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -5.274998523831063,
      "child_pnl": -5.274998523831063,
      "parent_quantity": 0.006793928485411424,
      "child_quantity": 0.006793928485411424
    },
    {
      "entry_timestamp_ms": 1737428400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": 18.551238774906317,
      "child_pnl": 9.275619387453158,
      "parent_quantity": 0.007832961568927689,
      "child_quantity": 0.0039164807844638445
    },
    {
      "entry_timestamp_ms": 1737568800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.491138375297165,
      "child_pnl": -23.469167590090056,
      "parent_quantity": 0.013648816469064552,
      "child_quantity": 0.013636051007885865
    },
    {
      "entry_timestamp_ms": 1738029600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.617341651850595,
      "child_pnl": -23.595252831278955,
      "parent_quantity": 0.011041814321434825,
      "child_quantity": 0.01103148713648205
    },
    {
      "entry_timestamp_ms": 1738476000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -7.890998865676208,
      "child_pnl": -7.883618574505239,
      "parent_quantity": 0.006422954351047492,
      "child_quantity": 0.0064169470921319255
    },
    {
      "entry_timestamp_ms": 1738627200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 19.70950768123695,
      "child_pnl": 19.69107377850802,
      "parent_quantity": 0.006575537175913564,
      "child_quantity": 0.006569387209377026
    },
    {
      "entry_timestamp_ms": 1740427200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 32.55603865770397,
      "child_pnl": 32.52558965514329,
      "parent_quantity": 0.005395019086624471,
      "child_quantity": 0.005389973234710155
    },
    {
      "entry_timestamp_ms": 1740484800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 4.263087029401291,
      "child_pnl": 4.259099850578972,
      "parent_quantity": 0.003268467140069128,
      "child_quantity": 0.0032654102090535404
    },
    {
      "entry_timestamp_ms": 1741564800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -24.23441547172546,
      "child_pnl": -24.211749514527373,
      "parent_quantity": 0.006891089730522943,
      "child_quantity": 0.006884644634083029
    },
    {
      "entry_timestamp_ms": 1741698000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.29631455643884,
      "child_pnl": -23.27452598599755,
      "parent_quantity": 0.017260479779950745,
      "child_quantity": 0.017244336403339614
    },
    {
      "entry_timestamp_ms": 1741651200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -24.239736864102994,
      "child_pnl": -24.21706592991456,
      "parent_quantity": 0.005636526111802005,
      "child_quantity": 0.005631254383265988
    },
    {
      "entry_timestamp_ms": 1741748400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.507022745988174,
      "child_pnl": -23.48503710445138,
      "parent_quantity": 0.012756047117256022,
      "child_quantity": 0.012744116645142353
    },
    {
      "entry_timestamp_ms": 1742284800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.59676348068909,
      "child_pnl": -11.585917263044749,
      "parent_quantity": 0.008207198449287273,
      "child_quantity": 0.008199522423059828
    },
    {
      "entry_timestamp_ms": 1742428800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.933805578759559,
      "child_pnl": -11.92264413247776,
      "parent_quantity": 0.004005546507898579,
      "child_quantity": 0.0040018002015018385
    },
    {
      "entry_timestamp_ms": 1742569200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -5.424244361318492,
      "child_pnl": -5.4191711755975875,
      "parent_quantity": 0.007360814815761741,
      "child_quantity": 0.007353930394977927
    },
    {
      "entry_timestamp_ms": 1742817600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.66087629277101,
      "child_pnl": -11.64997011171405,
      "parent_quantity": 0.0064567138252011064,
      "child_quantity": 0.006450674991734167
    },
    {
      "entry_timestamp_ms": 1743022800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -5.2713267369401064,
      "child_pnl": -5.266396571971363,
      "parent_quantity": 0.005994279249408131,
      "child_quantity": 0.005988672921619495
    },
    {
      "entry_timestamp_ms": 1742803200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.62173565223316,
      "child_pnl": -11.61086607862333,
      "parent_quantity": 0.006859319560994722,
      "child_quantity": 0.006852904178549911
    },
    {
      "entry_timestamp_ms": 1743440400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.61406229247721,
      "child_pnl": -6.607876294180625,
      "parent_quantity": 0.009927379746085832,
      "child_quantity": 0.009918094869185188
    },
    {
      "entry_timestamp_ms": 1743555600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.36228961706687,
      "child_pnl": -11.351662698070895,
      "parent_quantity": 0.009579692086653005,
      "child_quantity": 0.00957073239496742
    },
    {
      "entry_timestamp_ms": 1743764400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.916998388622279,
      "child_pnl": -6.9105290603399965,
      "parent_quantity": 0.0044539909407142475,
      "child_quantity": 0.004449825213336143
    },
    {
      "entry_timestamp_ms": 1743998400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.834280096100741,
      "child_pnl": -11.823211733984007,
      "parent_quantity": 0.004138038081296152,
      "child_quantity": 0.004134167858218391
    },
    {
      "entry_timestamp_ms": 1744412400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.426248223078204,
      "child_pnl": -11.415561484895424,
      "parent_quantity": 0.00807807015569517,
      "child_quantity": 0.008070514900541366
    },
    {
      "entry_timestamp_ms": 1744772400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -1.2988806117658718,
      "child_pnl": -1.2976657950773456,
      "parent_quantity": 0.00878908315788547,
      "child_quantity": 0.00878086290669354
    },
    {
      "entry_timestamp_ms": 1745611200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.812011401835642,
      "child_pnl": -11.800963867176932,
      "parent_quantity": 0.0038335070899942632,
      "child_quantity": 0.003829921688575286
    },
    {
      "entry_timestamp_ms": 1745222400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 41.19331725954046,
      "child_pnl": 41.15478998550978,
      "parent_quantity": 0.006150674410269266,
      "child_quantity": 0.006144921809259134
    },
    {
      "entry_timestamp_ms": 1745352000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 13.15658767231583,
      "child_pnl": 13.14428258274593,
      "parent_quantity": 0.0039307384342349705,
      "child_quantity": 0.003927062094312052
    },
    {
      "entry_timestamp_ms": 1746586800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.520327743703442,
      "child_pnl": -11.50955301485341,
      "parent_quantity": 0.006788857344344779,
      "child_quantity": 0.00678250786378188
    },
    {
      "entry_timestamp_ms": 1746684000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -9.85596137717338,
      "child_pnl": -9.84674329642446,
      "parent_quantity": 0.008912668402021588,
      "child_quantity": 0.00890433256405773
    },
    {
      "entry_timestamp_ms": 1746705600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 20.206196058141778,
      "child_pnl": 20.187297612849186,
      "parent_quantity": 0.00839101091715422,
      "child_quantity": 0.00838316297485419
    },
    {
      "entry_timestamp_ms": 1747324800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 1.3463363701510884,
      "child_pnl": 1.345077169054379,
      "parent_quantity": 0.00459048561983118,
      "child_quantity": 0.004586192231748475
    },
    {
      "entry_timestamp_ms": 1749513600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -23.45845628230516,
      "child_pnl": -23.436516063996667,
      "parent_quantity": 0.009457398404117134,
      "child_quantity": 0.009448553091232105
    },
    {
      "entry_timestamp_ms": 1750118400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": 13.55364092089619,
      "child_pnl": 6.770482237738533,
      "parent_quantity": 0.008383015612821156,
      "child_quantity": 0.004187587574183541
    },
    {
      "entry_timestamp_ms": 1750622400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -23.69183265721382,
      "child_pnl": -11.826610825708336,
      "parent_quantity": 0.006984631488539554,
      "child_quantity": 0.003486624254489378
    },
    {
      "entry_timestamp_ms": 1750694400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -22.9834214090132,
      "child_pnl": -22.973912587550977,
      "parent_quantity": 0.01253291679976781,
      "child_quantity": 0.012527731615798501
    },
    {
      "entry_timestamp_ms": 1752480000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.684582790844475,
      "child_pnl": -11.679748584063786,
      "parent_quantity": 0.004023108442677487,
      "child_quantity": 0.004021443981184838
    },
    {
      "entry_timestamp_ms": 1752192000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 1.3200719789579023,
      "child_pnl": 1.319525831865969,
      "parent_quantity": 0.0034834950835986285,
      "child_quantity": 0.003482053873770683
    },
    {
      "entry_timestamp_ms": 1752206400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -1.5981458921571403,
      "child_pnl": -1.5974846988696538,
      "parent_quantity": 0.003383506152757825,
      "child_quantity": 0.0033821063108739574
    },
    {
      "entry_timestamp_ms": 1753909200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -1.7379587179600073,
      "child_pnl": -1.7372396805780732,
      "parent_quantity": 0.010744906716606282,
      "child_quantity": 0.010740461277531813
    },
    {
      "entry_timestamp_ms": 1754092800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -10.935642912835924,
      "child_pnl": -5.465559280691765,
      "parent_quantity": 0.0065667445387891455,
      "child_quantity": 0.003282013855425299
    },
    {
      "entry_timestamp_ms": 1754884800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.652940969988288,
      "child_pnl": -11.654700559496971,
      "parent_quantity": 0.004056736520260446,
      "child_quantity": 0.004057349085881342
    },
    {
      "entry_timestamp_ms": 1755144000000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.674458754387569,
      "child_pnl": -11.676221593073251,
      "parent_quantity": 0.0036589980877545824,
      "child_quantity": 0.0036595505950284208
    },
    {
      "entry_timestamp_ms": 1755129600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.736509838206787,
      "child_pnl": -11.738282046581746,
      "parent_quantity": 0.003504728472127962,
      "child_quantity": 0.003505257684750444
    },
    {
      "entry_timestamp_ms": 1755504000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.425032690493389,
      "child_pnl": -11.426757865941404,
      "parent_quantity": 0.005223981220040612,
      "child_quantity": 0.005224770039152633
    },
    {
      "entry_timestamp_ms": 1755716400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.263005863678789,
      "child_pnl": -11.264706573139613,
      "parent_quantity": 0.006788047590665099,
      "child_quantity": 0.006789072583184653
    },
    {
      "entry_timestamp_ms": 1755633600000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.434098136691608,
      "child_pnl": -11.435824681018438,
      "parent_quantity": 0.0037101661476062354,
      "child_quantity": 0.0037107263812370104
    },
    {
      "entry_timestamp_ms": 1755648000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.461276376721484,
      "child_pnl": -11.463007024951889,
      "parent_quantity": 0.003661943036869575,
      "child_quantity": 0.003662495988829574
    },
    {
      "entry_timestamp_ms": 1756256400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.210495521296872,
      "child_pnl": -11.21218830171662,
      "parent_quantity": 0.006645129906672903,
      "child_quantity": 0.006646133318678316
    },
    {
      "entry_timestamp_ms": 1756180800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.542216418612314,
      "child_pnl": -11.543959288757241,
      "parent_quantity": 0.003183004617552416,
      "child_quantity": 0.0031834852499992446
    },
    {
      "entry_timestamp_ms": 1756724400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.28063290609919,
      "child_pnl": -11.282336277236489,
      "parent_quantity": 0.005666879720053138,
      "child_quantity": 0.00566773541666467
    },
    {
      "entry_timestamp_ms": 1757098800000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.140291696405015,
      "child_pnl": -10.141822876467625,
      "parent_quantity": 0.006761749991273424,
      "child_quantity": 0.006762771012865796
    },
    {
      "entry_timestamp_ms": 1758916800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -5.631334972037284,
      "child_pnl": -5.632185301405825,
      "parent_quantity": 0.006279578887302198,
      "child_quantity": 0.006280527101247286
    },
    {
      "entry_timestamp_ms": 1758844800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.370134940608715,
      "child_pnl": -6.371096828482279,
      "parent_quantity": 0.003810227830588853,
      "child_quantity": 0.0038108031734944477
    },
    {
      "entry_timestamp_ms": 1759334400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 13.842921741892187,
      "child_pnl": 13.845012017637101,
      "parent_quantity": 0.0039473928162929925,
      "child_quantity": 0.0039479888710575416
    },
    {
      "entry_timestamp_ms": 1759348800000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 13.228322527409277,
      "child_pnl": 13.230319998914247,
      "parent_quantity": 0.0037802451033176147,
      "child_quantity": 0.0037808159188431685
    },
    {
      "entry_timestamp_ms": 1759377600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 8.473945070952903,
      "child_pnl": 8.475224633329677,
      "parent_quantity": 0.0038843050479302798,
      "child_quantity": 0.0038848915764665907
    },
    {
      "entry_timestamp_ms": 1759435200000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": 0.3949047333919592,
      "child_pnl": 0.3949643638515654,
      "parent_quantity": 0.003663529764756259,
      "child_quantity": 0.003664082956311542
    },
    {
      "entry_timestamp_ms": 1760277600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.20791151403944,
      "child_pnl": -11.20807946224592,
      "parent_quantity": 0.006902737982733374,
      "child_quantity": 0.00690284141881623
    },
    {
      "entry_timestamp_ms": 1760155200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -10.103905006248798,
      "child_pnl": -5.052715345967742,
      "parent_quantity": 0.0037313628832491333,
      "child_quantity": 0.0018659631587893304
    },
    {
      "entry_timestamp_ms": 1760328000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -10.09742218091616,
      "child_pnl": -10.104287447564799,
      "parent_quantity": 0.006140749953055173,
      "child_quantity": 0.006144925066771821
    },
    {
      "entry_timestamp_ms": 1760500800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 0.16563063434424485,
      "child_pnl": 0.16574324709327923,
      "parent_quantity": 0.005001173936371389,
      "child_quantity": 0.0050045742490466665
    },
    {
      "entry_timestamp_ms": 1760623200000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 53.65061003284475,
      "child_pnl": 53.68708723832734,
      "parent_quantity": 0.012274838618806499,
      "child_quantity": 0.012283184317211227
    },
    {
      "entry_timestamp_ms": 1760644800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -1.31564373441536,
      "child_pnl": -0.6582691222045269,
      "parent_quantity": 0.005389967441011182,
      "child_quantity": 0.002696816047759371
    },
    {
      "entry_timestamp_ms": 1760659200000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": true,
      "parent_pnl": -1.3410152790939152,
      "child_pnl": -0.7646893073153507,
      "parent_quantity": 0.005044713314713517,
      "child_quantity": 0.0028766550168162876
    },
    {
      "entry_timestamp_ms": 1761069600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 22.24950423474413,
      "child_pnl": 22.267496072031054,
      "parent_quantity": 0.008663700771703546,
      "child_quantity": 0.00867070658598788
    },
    {
      "entry_timestamp_ms": 1761537600000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.670699913369159,
      "child_pnl": -11.680137307193778,
      "parent_quantity": 0.004732955667449031,
      "child_quantity": 0.004736782924333343
    },
    {
      "entry_timestamp_ms": 1761494400000,
      "sleeve": "swing",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -7.268434602239325,
      "child_pnl": -7.274312148602354,
      "parent_quantity": 0.004705734478088275,
      "child_quantity": 0.004709539722832246
    },
    {
      "entry_timestamp_ms": 1761930000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -16.75266621680061,
      "child_pnl": -16.766213091441713,
      "parent_quantity": 0.007526112259476927,
      "child_quantity": 0.007532198174279655
    },
    {
      "entry_timestamp_ms": 1762286400000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.674335153411858,
      "child_pnl": -11.683775486836687,
      "parent_quantity": 0.0026909978710583995,
      "child_quantity": 0.0026931739193570363
    },
    {
      "entry_timestamp_ms": 1762376400000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 38.58421186446337,
      "child_pnl": 38.615412598393675,
      "parent_quantity": 0.016651169622055734,
      "child_quantity": 0.016664634422498756
    },
    {
      "entry_timestamp_ms": 1762560000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 6.998624692498839,
      "child_pnl": 7.0042840597984934,
      "parent_quantity": 0.016117263588261602,
      "child_quantity": 0.016130296650973066
    },
    {
      "entry_timestamp_ms": 1763622000000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 76.20437453834748,
      "child_pnl": 76.26599643754939,
      "parent_quantity": 0.01294806787815455,
      "child_quantity": 0.01295853820270587
    },
    {
      "entry_timestamp_ms": 1763121600000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": 33.86918625515065,
      "child_pnl": 33.89657423115739,
      "parent_quantity": 0.0025150059317775152,
      "child_quantity": 0.0025170396659687476
    },
    {
      "entry_timestamp_ms": 1763712000000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -6.588385000279523,
      "child_pnl": -6.593712631387968,
      "parent_quantity": 0.002397025393602536,
      "child_quantity": 0.002398963724021015
    },
    {
      "entry_timestamp_ms": 1764572400000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": true,
      "parent_pnl": -22.649031699159423,
      "child_pnl": -11.333673305151256,
      "parent_quantity": 0.019793092979120065,
      "child_quantity": 0.009904549232104936
    },
    {
      "entry_timestamp_ms": 1764748800000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -22.865099543750855,
      "child_pnl": -22.910309511396896,
      "parent_quantity": 0.015001109967920083,
      "child_quantity": 0.01503077087952061
    },
    {
      "entry_timestamp_ms": 1764882000000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -10.232581080310162,
      "child_pnl": -10.252813428684203,
      "parent_quantity": 0.005371522645010557,
      "child_quantity": 0.005382143476314013
    },
    {
      "entry_timestamp_ms": 1765429200000,
      "sleeve": "intraday",
      "direction": 1,
      "extra_guard": false,
      "parent_pnl": -11.42670840834077,
      "child_pnl": -11.449301842340622,
      "parent_quantity": 0.007126984520988436,
      "child_quantity": 0.007141076335414661
    },
    {
      "entry_timestamp_ms": 1765893600000,
      "sleeve": "intraday",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -11.429278415097452,
      "child_pnl": -11.45187693063749,
      "parent_quantity": 0.007320907524037923,
      "child_quantity": 0.007335382772294246
    },
    {
      "entry_timestamp_ms": 1765828800000,
      "sleeve": "swing",
      "direction": -1,
      "extra_guard": false,
      "parent_pnl": -23.180912707908526,
      "child_pnl": -23.226747116436886,
      "parent_quantity": 0.00863169689272414,
      "child_quantity": 0.008648763896368874
    }
  ]
}
```

from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite
import json
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.backtest.reviews import ComparisonReviewRepository
from app.backtest.directional_evidence import load_directional_evidence, directional_equity_points, portfolio_position_points, MODES
from app.backtest.catalog import VersionCatalogRepository, CATEGORY_LABELS, CATEGORY_ORDER, group_versions
from app.backtest.engine import BacktestEngine
from app.backtest.configuration import make_strategy, strategy_family
from app.backtest.comparison import load_comparison, load_saved_result, comparison_warnings, comparison_chart
from app.backtest.reproduction import config_for_run
from app.backtest.research import ResearchPlanRepository
from app.backtest.periods import annual_performance
from app.backtest.advisor import ResearchAdvice, analyze_backtest
from app.backtest.models import BacktestConfig, BacktestResult
from app.backtest.optimization import (
    OptimizationRequest,
    OptimizationRequestRepository,
)
from app.backtest.runs import (
    BacktestRun,
    BacktestRunRepository,
    StrategyVersion,
)
from app.config.settings import Settings
from app.data.downloader import download_candles
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from app.exchange.ccxt_client import CcxtHistoricalProvider

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[1] / "templates"
)


@router.get("/derivatives-research", response_class=HTMLResponse)
def derivatives_research(
    request: Request, year: int = Query(default=0,ge=0), cost: int = Query(default=1,ge=1,le=2),
    mode: str = Query(default="both",pattern=r"^(both|long_only|short_only|all)$"),
    experiment: str = Query(default="",pattern=r"^([0-9a-f]{64})?$"),
) -> HTMLResponse:
    error=None
    try:
        entries=load_directional_evidence(Settings.from_env().db_path.parent)
    except ValueError as exc:
        entries=[]
        error=str(exc)
    selected=next((e for e in entries if e['id']==experiment),None)
    if experiment and selected is None and not error:
        raise HTTPException(status_code=404,detail="找不到保存的合約研究結果")
    visible=[e for e in entries if (not year or e['year']==year) and e['cost']==cost and (mode=='all' or e['mode']==mode)]
    for entry in visible:
        entry['url']='/derivatives-research?'+urlencode(dict(year=year,cost=cost,mode=mode,experiment=entry['id']))+'#directional-result'
    result=selected['row'].get('result') if selected else None
    return templates.TemplateResponse(request=request,name="derivatives_research.html",context=dict(
        entries=visible,selected=selected,result=result,error=error,year=year,cost=cost,mode=mode,modes=MODES,
        years=sorted({e['year'] for e in entries},reverse=True),
        chart_points=directional_equity_points(result) if result else "",
        position_points=portfolio_position_points(result) if result else "",
        format_time=lambda t:datetime.fromtimestamp(t/1000,timezone.utc).strftime('%Y-%m-%d %H:%M'),
    ),status_code=503 if error else 200)


def _utc_ms(value: date) -> int:
    point = datetime.combine(value, time.min, tzinfo=timezone.utc)
    return int(point.timestamp() * 1000)


def _format_date(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc).date().isoformat()


def _chart_points(result: BacktestResult, width: int = 900, height: int = 260) -> str:
    values = [point.equity for point in result.equity_curve]
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = high - low or 1.0
    return " ".join(
        f"{index * width / (len(values) - 1):.1f},{height - (value - low) * height / span:.1f}"
        for index, value in enumerate(values)
    )


def _validate_range_coverage(
    candles: list[Candle], timeframe: str, since_ms: int, until_ms: int
) -> None:
    interval = TIMEFRAMES_MS[timeframe]
    expected_count = (until_ms - since_ms) // interval
    if not candles:
        raise ValueError("這個市場與期間沒有資料，請先下載 K 線")
    has_full_boundaries = (
        candles[0].timestamp_ms == since_ms
        and candles[-1].timestamp_ms == until_ms - interval
    )
    if len(candles) != expected_count or not has_full_boundaries:
        available = {candle.timestamp_ms for candle in candles}
        missing = []
        for timestamp in range(since_ms, until_ms, interval):
            if timestamp not in available:
                missing.append(
                    datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime(
                        "%Y-%m-%d %H:%M UTC"
                    )
                )
                if len(missing) == 3:
                    break
        missing_detail = f"缺少時間（最多列出 3 筆）：{'、'.join(missing)}。" if missing else ""
        actual_range = (
            f"{_format_date(candles[0].timestamp_ms)}～"
            f"{_format_date(candles[-1].timestamp_ms)}"
        )
        raise ValueError(
            "選擇區間的 K 線資料不完整："
            f"需要 {expected_count:,} 根，目前只有 {len(candles):,} 根，"
            f"實際覆蓋 {actual_range}。{missing_detail}"
            "請先下載完整區間；若重複下載仍缺少相同時間，可能是來源缺漏，"
            "請改用完整區間，或另行核實來源。系統不會自動補造 K 線。"
        )


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    settings = Settings.from_env()
    coverage = CandleRepository(settings.db_path).list_coverage(settings.exchange_id)
    run_repository = BacktestRunRepository(settings.db_path)
    strategy_versions = run_repository.list_strategy_versions()
    versions_by_key = {
        version.strategy_key: version.version_number for version in strategy_versions
    }
    history = [
        _history_item(run, versions_by_key.get(run.strategy_key or ""))
        for run in run_repository.list_recent()
    ]
    optimization_requests = OptimizationRequestRepository(settings.db_path).list_requests(limit=500)
    pending_run_keys = {
        item.base_run_key
        for item in optimization_requests if item.status == "pending"
    }
    status_by_strategy = {}
    for item in optimization_requests:
        status_by_strategy.setdefault(item.strategy_key, item)
    adjustments = [
        _strategy_version_item(version, run_repository, versions_by_key)
        for version in strategy_versions
    ]
    categories = VersionCatalogRepository(settings.db_path).categories(strategy_versions)
    for item in adjustments:
        item["category"] = categories[item["version"].strategy_key]
        item["category_label"] = CATEGORY_LABELS[item["category"]]
        item["optimization_request"] = status_by_strategy.get(item["version"].strategy_key)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "coverage": coverage,
            "research_plans": ResearchPlanRepository(settings.db_path).list_plans(),
            "format_date": _format_date,
            "exchange": settings.exchange_id,
            "live_trading": settings.live_trading,
            "notice": request.query_params.get("notice"),
            "notice_kind": request.query_params.get("kind", "success"),
            "development_branch_draft": (
                request.query_params.get("load_strategy") == "development_branch"
            ),
            "today": date.today().isoformat(),
            "default_since": (date.today() - timedelta(days=365)).isoformat(),
            "history": history,
            "history_versions": sorted(
                {
                    item["version_number"]
                    for item in history
                    if item["version_number"] is not None
                }
            ),
            "adjustments": sorted(adjustments, key=lambda item: (CATEGORY_ORDER[item["category"]], -item["version"].created_at_ms)),
            "version_groups": group_versions(adjustments),
            "category_labels": CATEGORY_LABELS,
            "adjustment_versions": sorted(
                {item["version"].version_number for item in adjustments}
            ),
            "pending_run_keys": pending_run_keys,
        },
    )


@router.post("/strategies/{strategy_key}/classification")
def classify_strategy_version(strategy_key: str, category: str = Form(...)) -> RedirectResponse:
    repository = BacktestRunRepository(Settings.from_env().db_path)
    if repository.get_strategy_version(strategy_key) is None:
        raise HTTPException(status_code=404, detail="找不到策略版本")
    try:
        VersionCatalogRepository(Settings.from_env().db_path).set_category(strategy_key, category)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse("/#strategy-adjustments", status_code=303)


@router.get("/strategy-optimizations", response_class=HTMLResponse)
def strategy_optimizations(request: Request) -> HTMLResponse:
    settings = Settings.from_env()
    run_repository = BacktestRunRepository(settings.db_path)
    requests = OptimizationRequestRepository(settings.db_path).list_requests()
    items = [
        _optimization_item(item, run_repository) for item in requests
    ]
    return templates.TemplateResponse(
        request=request,
        name="strategy_optimizations.html",
        context={
            "pending": [item for item in items if item["request"].status == "pending"],
            "history": [item for item in items if item["request"].status != "pending"],
            "notice": request.query_params.get("notice"),
            "notice_kind": request.query_params.get("kind", "success"),
        },
    )


@router.get("/strategies/{strategy_key}/backtests", response_class=HTMLResponse)
def strategy_backtests(request: Request, strategy_key: str) -> HTMLResponse:
    repository = BacktestRunRepository(Settings.from_env().db_path)
    version = repository.get_strategy_version(strategy_key)
    if version is None:
        raise HTTPException(status_code=404, detail="找不到策略版本")
    runs = repository.list_runs_for_strategy(strategy_key, limit=None)
    experiments = [_history_item(run, version.version_number) for run in runs]
    return templates.TemplateResponse(
        request=request, name="strategy_backtests.html",
        context={"version": version, "experiments": experiments, "format_date": _format_date},
    )


@router.get("/backtests/select", response_class=HTMLResponse)
def select_backtests(
    request: Request, symbol: str = Query(default="BTC/USDT", pattern=r"^(BTC|ETH)/USDT$"),
    timeframe: str = Query(default="4h", pattern=r"^(1h|4h|1d)$"),
    since: date | None = None, until: date | None = None,
    period: str = Query(default="", max_length=50),
    period_a: str = Query(default="", max_length=50),
) -> HTMLResponse:
    repository = BacktestRunRepository(Settings.from_env().db_path)
    periods = repository.list_periods(symbol, timeframe)
    options = []
    for stored_period in periods:
        start, end = stored_period["since_ms"], stored_period["until_exclusive_ms"]
        def label(timestamp: int) -> str:
            return datetime.fromtimestamp(timestamp/1000, timezone.utc).strftime(
                "%Y-%m-%d" if timestamp % TIMEFRAMES_MS["1d"] == 0 else "%Y-%m-%d %H:%M"
            )
        options.append(dict(value=f"{start}:{end}", label=f"{label(start)} → {label(end)}",
                            count=stored_period["run_count"], since=start, until=end))
    by_value = {option["value"]: option for option in options}
    selected_value = period or period_a or (options[0]["value"] if options else "")
    selected_period = by_value.get(selected_value)
    error = ""
    if since is not None or until is not None:
        if since is None or until is None or since >= until:
            selected_period = None
            error = "請輸入開始與結束日期，結束日期必須晚於開始日期。"
        else:
            selected_period = dict(since=_utc_ms(since), until=_utc_ms(until),
                                   label=f"{since} → {until}")
    elif options and selected_period is None:
        error = "選取區間不屬於目前交易對／週期，請重新選擇區間。"
    since_value = str(since) if since else (_format_date(selected_period["since"]) if selected_period else "")
    until_value = str(until) if until else (_format_date(selected_period["until"]) if selected_period else "")
    experiments = []
    if selected_period is not None:
        for run in repository.list_runs_in_period(symbol, timeframe, selected_period["since"], selected_period["until"]):
            version = repository.get_strategy_version_for_run(run.run_key)
            experiments.append(_history_item(run, version.version_number if version else None))
    return templates.TemplateResponse(
        request=request, name="select_backtests.html",
        context=dict(symbol=symbol, timeframe=timeframe, options=options, since_value=since_value, until_value=until_value,
                     selected_value=selected_value, selected_period=selected_period,
                     experiments=experiments,
                     version_count=len({item["run"].strategy_key for item in experiments}), error=error),
    )


@router.get("/backtests/compare", response_class=HTMLResponse)
def compare_backtests(
    request: Request, run_keys: list[str] = Query(default=[]),
    chart_mode: str = Query(default="equity", pattern=r"^(equity|indexed)$"),
    left_run_key: str = Query(default="", max_length=64),
    right_run_key: str = Query(default="", max_length=64),
) -> HTMLResponse:
    settings = Settings.from_env()
    if not run_keys and (left_run_key or right_run_key):
        run_keys = [left_run_key, right_run_key]
    try:
        entries = load_comparison(settings.db_path, settings.exchange_id, run_keys)
    except ValueError as exc:
        return templates.TemplateResponse(request=request, name="backtest_comparison.html",
                                          context={"error": str(exc)}, status_code=400)
    rows = []
    fields = [
        ("初始資金", "initial_cash", ",.2f"), ("最終資產", "final_equity", ",.2f"),
        ("淨盈虧（USDT）", "net_pnl", "+,.2f"), ("總報酬", "total_return", "+.2%"),
        ("CAGR", "cagr", ".2%"), ("Sharpe", "sharpe_ratio", ".3f"),
        ("Sortino", "sortino_ratio", ".3f"), ("最大回撤", "maximum_drawdown", ".2%"),
        ("勝率", "win_rate", ".2%"), ("Profit Factor", "profit_factor", ".3f"),
        ("平均獲利", "average_win", ",.2f"), ("平均虧損", "average_loss", ",.2f"),
        ("交易次數", "number_of_trades", "d"), ("持倉時間比例", "exposure", ".2%"),
        ("手續費", "fees", ",.2f"), ("模擬滑價成本", "slippage", ",.2f"),
    ]
    for label, field, spec in fields:
        values = []
        for entry in entries:
            if field == "net_pnl":
                value = entry.run.final_equity - entry.run.initial_cash
            elif hasattr(entry.run, field):
                value = getattr(entry.run, field)
            else:
                value = getattr(entry.result.metrics, field) if entry.result else None
            values.append("—" if value is None else ("∞" if not isfinite(value) else format(value, spec)))
        rows.append(dict(label=label, values=values))
    return templates.TemplateResponse(
        request=request, name="backtest_comparison.html",
        context=dict(entries=entries, policies=[json.loads(entry.run.policy_json) for entry in entries], rows=rows, reviews=ComparisonReviewRepository(settings.db_path).for_pair(run_keys), warnings=comparison_warnings(entries),
                     chart=comparison_chart(entries, chart_mode), chart_mode=chart_mode,
                     selection_url="/backtests/select?" + urlencode(dict(
                         symbol=entries[0].run.symbol, timeframe=entries[0].run.timeframe,
                         since=_format_date(entries[0].run.since_ms),
                         until=_format_date(entries[0].run.until_ms + TIMEFRAMES_MS[entries[0].run.timeframe]),
                     )) if (entries[0].run.symbol, entries[0].run.timeframe) == (entries[1].run.symbol, entries[1].run.timeframe) else "/backtests/select",
                     format_date=_format_date, intervals=TIMEFRAMES_MS),
    )


@router.post("/comparison-reviews")
def enqueue_comparison_review(run_keys: list[str] = Form(...), objective: str = Form("", max_length=1000)) -> RedirectResponse:
    settings = Settings.from_env()
    try:
        item = ComparisonReviewRepository(settings.db_path).enqueue(settings.exchange_id, run_keys, objective)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(f"/comparison-reviews#review-{item['request_id']}", status_code=303)


@router.get("/comparison-reviews", response_class=HTMLResponse)
def comparison_reviews(request: Request) -> HTMLResponse:
    items = ComparisonReviewRepository(Settings.from_env().db_path).list_requests()
    return templates.TemplateResponse(request=request, name="comparison_reviews.html", context=dict(items=items))


@router.post("/comparison-reviews/{request_id}/cancel")
def cancel_comparison_review(request_id: int) -> RedirectResponse:
    try:
        ComparisonReviewRepository(Settings.from_env().db_path).finish(request_id, "cancelled", "使用者取消")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RedirectResponse("/comparison-reviews", status_code=303)


@router.get("/backtests/results/{run_key}", response_class=HTMLResponse)
def saved_backtest_result(request: Request, run_key: str) -> HTMLResponse:
    settings = Settings.from_env()
    try:
        entry = load_saved_result(settings.db_path, settings.exchange_id, run_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    run = entry.run
    if entry.result is None:
        return templates.TemplateResponse(
            request=request, name="saved_result_unavailable.html",
            context=dict(entry=entry, format_date=_format_date, intervals=TIMEFRAMES_MS),
        )
    result = entry.result
    metrics = {key: value if not isinstance(value, float) or isfinite(value) else None
               for key, value in asdict(result.metrics).items()}
    return templates.TemplateResponse(
        request=request, name="backtest_result.html",
        context=dict(saved_view=True, snapshot_source=entry.source, result=result,
                     metrics=metrics, chart_points=_chart_points(result),
                     annual_performance=annual_performance(result),
                     first_date=_format_date(run.since_ms), last_date=_format_date(run.until_ms),
                     candle_count=run.candle_count, values=_history_item(run)["parameters"],
                     format_date=_format_date, saved_run=run, saved_version=entry.version,
                     version_run_count=len(BacktestRunRepository(settings.db_path).list_runs_for_strategy(run.strategy_key, limit=None))),
    )


@router.get("/backtests/results/{run_key}/matches", response_class=HTMLResponse)
def matching_backtests(request: Request, run_key: str) -> HTMLResponse:
    repository = BacktestRunRepository(Settings.from_env().db_path)
    run = repository.get_run(run_key)
    if run is None:
        raise HTTPException(status_code=404, detail="找不到回測紀錄")
    version = repository.get_strategy_version_for_run(run_key)
    matches = []
    for candidate in repository.list_matching_period(run):
        candidate_version = repository.get_strategy_version_for_run(candidate.run_key)
        item = _history_item(candidate, candidate_version.version_number if candidate_version else None)
        item["compare_url"] = "/backtests/compare?" + urlencode({"run_keys": [run_key, candidate.run_key]}, doseq=True)
        matches.append(item)
    return templates.TemplateResponse(
        request=request, name="matching_backtests.html",
        context=dict(source=_history_item(run, version.version_number if version else None),
                     matches=matches),
    )


@router.post("/strategy-optimizations/enqueue")
def enqueue_strategy_optimization(
    run_key: str = Form(default="", max_length=64),
    strategy_key: str = Form(default="", max_length=64),
    objective: str = Form(default="", max_length=300),
) -> RedirectResponse:
    settings = Settings.from_env()
    if not strategy_key:
        run = BacktestRunRepository(settings.db_path).get_run(run_key)
        if run is None:
            return _optimization_redirect("找不到指定的策略版本", "error")
        strategy_key = run.strategy_key
    try:
        item = OptimizationRequestRepository(settings.db_path).enqueue_version(strategy_key, objective)
        return _optimization_redirect(f"已標記等待 AI 優化，將參考此版本 {len(item.evidence_run_keys)} 筆回測；任務 #{item.request_id}")
    except ValueError as exc:
        return _optimization_redirect(str(exc), "error")


@router.post("/strategy-optimizations/{request_id}/cancel")
def cancel_strategy_optimization(request_id: int) -> RedirectResponse:
    settings = Settings.from_env()
    cancelled = OptimizationRequestRepository(settings.db_path).cancel(request_id)
    return _optimization_redirect(
        "已取消優化任務" if cancelled else "任務已處理，無法取消",
        "warning" if cancelled else "error",
    )


def _optimization_redirect(message: str, kind: str = "success") -> RedirectResponse:
    query = urlencode({"notice": message, "kind": kind})
    return RedirectResponse(f"/strategy-optimizations?{query}", status_code=303)


def _dashboard_redirect(
    message: str, kind: str = "success", anchor: str = "market-data"
) -> RedirectResponse:
    query = urlencode({"notice": message, "kind": kind})
    return RedirectResponse(url=f"/?{query}#{anchor}", status_code=303)


@router.post("/data/download", response_class=HTMLResponse)
def download_market_data(
    symbol: str = Form(pattern=r"^(BTC|ETH)/USDT$"),
    timeframe: str = Form(pattern=r"^(1h|4h|1d)$"),
    since: date = Form(),
    until: date = Form(),
    return_to: str = Form(default="market-data", pattern=r"^(market-data|backtest)$"),
) -> RedirectResponse:
    try:
        if until <= since:
            raise ValueError("結束日期必須晚於開始日期")
        settings = Settings.from_env()
        candles = download_candles(
            CcxtHistoricalProvider(settings.exchange_id),
            symbol,
            timeframe,
            _utc_ms(since),
            _utc_ms(until),
        )
        repository = CandleRepository(settings.db_path)
        count = repository.upsert(candles)
        if count == 0:
            return _dashboard_redirect(
                "指定期間沒有可下載的已完成 K 線", "warning", return_to
            )
        interval = TIMEFRAMES_MS[timeframe]
        closed_until_ms = min(
            _utc_ms(until),
            int(datetime.now(timezone.utc).timestamp() * 1000) // interval * interval,
        )
        if closed_until_ms > _utc_ms(since):
            stored = repository.list_range(
                settings.exchange_id, symbol, timeframe, _utc_ms(since), closed_until_ms
            )
            try:
                _validate_range_coverage(stored, timeframe, _utc_ms(since), closed_until_ms)
            except ValueError as exc:
                return _dashboard_redirect(
                    f"已同步 {symbol} {timeframe}，共 {count:,} 根；但{exc}",
                    "warning", return_to,
                )
        return _dashboard_redirect(
            f"已同步 {symbol} {timeframe}，共 {count:,} 根已完成 K 線",
            anchor=return_to,
        )
    except Exception as exc:
        return _dashboard_redirect(f"下載失敗：{exc}", "error", return_to)


@router.post("/research-plans")
def create_research_plan(
    name: str = Form(max_length=100),
    development_since: date = Form(), development_until: date = Form(),
    validation_since: date = Form(), validation_until: date = Form(),
    holdout_since: date = Form(), holdout_until: date = Form(),
    note: str = Form(default="", max_length=1000),
) -> RedirectResponse:
    try:
        ResearchPlanRepository(Settings.from_env().db_path).create(
            name, *map(_utc_ms, (development_since, development_until,
                                validation_since, validation_until, holdout_since, holdout_until)), note,
        )
        return _dashboard_redirect("已鎖定研究時段；已看過的歷史驗證只作回溯比較", anchor="research-plan")
    except ValueError as exc:
        return _dashboard_redirect(str(exc), "error", "research-plan")


@router.post("/data/delete", response_class=HTMLResponse)
def delete_market_data(
    symbol: str = Form(pattern=r"^(BTC|ETH)/USDT$"),
    timeframe: str = Form(pattern=r"^(1h|4h|1d)$"),
) -> RedirectResponse:
    settings = Settings.from_env()
    deleted = CandleRepository(settings.db_path).delete_dataset(
        settings.exchange_id, symbol, timeframe
    )
    return _dashboard_redirect(
        f"已刪除 {symbol} {timeframe} 的 {deleted:,} 根 K 線",
        "warning",
    )


@router.get("/backtests/run", response_class=HTMLResponse)
def run_backtest(
    request: Request,
    symbol: str = Query(pattern=r"^(BTC|ETH)/USDT$"),
    timeframe: str = Query(pattern=r"^(1h|4h|1d)$"),
    since: date = Query(),
    until: date = Query(),
    strategy: str = Query(pattern=r"^(sma|buy-hold|momentum|mean-reversion|intraday)$"),
    lookback: int = Query(default=20, ge=2, le=1000),
    momentum_threshold: float = Query(default=0, ge=0, lt=1),
    entry_deviation: float = Query(default=0.05, gt=0, lt=1),
    fast: int = Query(default=20, ge=1, le=500),
    slow: int = Query(default=60, ge=2, le=1000),
    initial_cash: float = Query(default=10_000, gt=0, le=1_000_000_000),
    fee_bps: float = Query(default=10, ge=0, le=1000),
    slippage_bps: float = Query(default=5, ge=0, le=1000),
    stop_loss_pct: float = Query(default=5, ge=0, lt=100),
    take_profit_pct: float = Query(default=10, ge=0, lt=1000),
    leverage: float = Query(default=1, ge=1, le=10),
    stage: str = Query(
        default="development", pattern=r"^(development|validation|out_of_sample)$"
    ),
    note: str = Query(default="", max_length=200),
    base_run_key: str = Query(default="", max_length=64),
    intraday_strong_close: bool = Query(default=False),
    intraday_min_atr_pct: float = Query(default=0, ge=0, lt=100),
    intraday_entry: str = Query(default="breakout", pattern=r"^(breakout|pullback)$"),
    max_entries_per_day: int = Query(default=0, ge=0),
    max_holding_bars: int = Query(default=0, ge=0),
    higher_timeframe_filter: bool = Query(default=False),
    risk_regime: str = Query(default="fixed", pattern=r"^(fixed|slow_slope|loss_streak)$"),
    risk_per_trade_pct: float = Query(default=0, ge=0, le=100),
    max_exposure_pct: float = Query(default=100, gt=0, le=100),
    exit_mode: str = Query(default="fixed", pattern=r"^(fixed|signal)$"),
    trailing_reentry_mode: str = Query(default="inherit", pattern=r"^(inherit|exit_high_breakout|pullback_reclaim)$"),
    trailing_activation_pct: float = Query(default=0, ge=0, lt=100),
    trailing_distance_pct: float = Query(default=0, ge=0, lt=100),
    trend_entry_buffer_pct: float = Query(default=0, ge=0, lt=100),
    stop_reentry_mode: str = Query(default="immediate", pattern=r"^(immediate|signal_reset)$"),
    research_plan_id: str = Query(default="", max_length=64),
    strategy_key: str = Query(default="", max_length=64),
) -> HTMLResponse:
    values = {
        "symbol": symbol,
        "timeframe": timeframe,
        "since": since.isoformat(),
        "until": until.isoformat(),
        "strategy": strategy,
        "fast": fast,
        "slow": slow,
        "initial_cash": initial_cash,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct,
        "leverage": leverage,
        "stage": stage,
        "note": note,
        "base_run_key": base_run_key,
        "intraday_strong_close": intraday_strong_close,
        "intraday_min_atr_pct": intraday_min_atr_pct,
        "intraday_entry": intraday_entry,
        "max_entries_per_day": max_entries_per_day,
        "max_holding_bars": max_holding_bars,
        "higher_timeframe_filter": higher_timeframe_filter,
        "risk_regime": risk_regime,
        "risk_per_trade_pct": risk_per_trade_pct,
        "max_exposure_pct": max_exposure_pct,
        "exit_mode": exit_mode,
        "stop_reentry_mode": stop_reentry_mode,
        "trend_entry_buffer_pct": trend_entry_buffer_pct,
        "trailing_reentry_mode": trailing_reentry_mode,
        "trailing_activation_pct": trailing_activation_pct,
        "trailing_distance_pct": trailing_distance_pct,
        "research_plan_id": research_plan_id,
        "lookback": lookback,
        "momentum_threshold": momentum_threshold,
        "entry_deviation": entry_deviation,
        "strategy_key": strategy_key,
    }
    try:
        if strategy_key:
            repo = BacktestRunRepository(Settings.from_env().db_path)
            selected_runs = repo.list_runs_for_strategy(strategy_key, limit=None)
            if not selected_runs:
                raise ValueError("找不到選擇的策略版本")
            selected = selected_runs[0]
            if (selected.symbol, selected.timeframe) != (symbol, timeframe):
                raise ValueError("選擇的版本與交易對／週期不符")
            stored_config = config_for_run(selected)
            strategy = strategy_family(selected.strategy_name)
            fast, slow = selected.fast_period or 20, selected.slow_period or 60
            stop_loss_pct = (stored_config.stop_loss_pct or 0) * 100
            take_profit_pct = (stored_config.take_profit_pct or 0) * 100
            intraday_strong_close = stored_config.intraday_strong_close
            intraday_min_atr_pct = stored_config.intraday_min_atr_fraction * 100
            intraday_entry = stored_config.intraday_entry
            max_entries_per_day = stored_config.max_entries_per_day or 0
            max_holding_bars = stored_config.max_holding_bars or 0
            higher_timeframe_filter = stored_config.higher_timeframe_filter
            risk_regime = stored_config.risk_regime
            risk_per_trade_pct = (stored_config.risk_per_trade or 0) * 100
            max_exposure_pct = stored_config.max_exposure_fraction * 100
            exit_mode, leverage = stored_config.exit_mode, stored_config.leverage
            stop_reentry_mode = stored_config.stop_reentry_mode
            trend_entry_buffer_pct = stored_config.trend_entry_buffer * 100
            trailing_reentry_mode = stored_config.trailing_reentry_mode
            trailing_activation_pct = (stored_config.trailing_activation or 0) * 100
            trailing_distance_pct = (stored_config.trailing_distance or 0) * 100
            if strategy == "momentum":
                _, period, threshold = selected.strategy_name.split("_")
                lookback, momentum_threshold = int(period), float(threshold)
            elif strategy == "mean-reversion":
                _, _, period, deviation = selected.strategy_name.split("_")
                lookback, entry_deviation = int(period), float(deviation)
            base_run_key = selected.run_key
            research_plan_id, stage = "", "development"
            values.update(strategy=strategy, fast=fast, slow=slow,
                          stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct,
                          intraday_strong_close=intraday_strong_close, intraday_min_atr_pct=intraday_min_atr_pct, intraday_entry=intraday_entry, max_entries_per_day=max_entries_per_day, max_holding_bars=max_holding_bars, higher_timeframe_filter=higher_timeframe_filter, risk_regime=risk_regime, risk_per_trade_pct=risk_per_trade_pct, max_exposure_pct=max_exposure_pct,
                          exit_mode=exit_mode, stop_reentry_mode=stop_reentry_mode, trend_entry_buffer_pct=trend_entry_buffer_pct, trailing_activation_pct=trailing_activation_pct, trailing_distance_pct=trailing_distance_pct, trailing_reentry_mode=trailing_reentry_mode, leverage=leverage, lookback=lookback,
                          momentum_threshold=momentum_threshold, entry_deviation=entry_deviation,
                          base_run_key=base_run_key, research_plan_id="", stage=stage)
        if until <= since:
            raise ValueError("結束日期必須晚於開始日期")
        if base_run_key and (
            len(base_run_key) != 64
            or any(character not in "0123456789abcdef" for character in base_run_key)
        ):
            raise ValueError("策略基準版本識別碼無效")
        settings = Settings.from_env()
        since_ms, until_ms = _utc_ms(since), _utc_ms(until)
        if leverage != 1:
            raise ValueError("研究介面目前固定 1 倍槓桿；先驗證風控與策略")
        if research_plan_id:
            ResearchPlanRepository(settings.db_path).validate(research_plan_id, stage, since_ms, until_ms)
        elif stage == "out_of_sample":
            raise ValueError("未見資料測試必須先登記研究計畫與保留時段")
        candle_repository = CandleRepository(settings.db_path)
        candles = candle_repository.list_range(
            settings.exchange_id, symbol, timeframe, since_ms, until_ms
        )
        _validate_range_coverage(candles, timeframe, since_ms, until_ms)
        warmup_required = slow if strategy == "sma" else (lookback + 1 if strategy == "momentum" else lookback if strategy == "mean-reversion" else 1)
        if strategy == "intraday":
            if timeframe != "1h":
                raise ValueError("短線策略需選1H")
            warmup_required = max(warmup_required, 243)
        if higher_timeframe_filter and timeframe != "1h":
            raise ValueError("4H方向濾網需選1H進場週期")
        if higher_timeframe_filter:
            warmup_required = max(warmup_required, 243)
        if risk_regime == "slow_slope" or trailing_reentry_mode == "pullback_reclaim":
            warmup_required = max(warmup_required, 186)
        interval = TIMEFRAMES_MS[timeframe]
        warmup_since_ms = max(0, since_ms - warmup_required * interval)
        warmup_candles = (
            candle_repository.list_range(
                settings.exchange_id,
                symbol,
                timeframe,
                warmup_since_ms,
                since_ms,
            )
            if warmup_since_ms < since_ms
            else []
        )
        signal_candles = warmup_candles + candles
        config = BacktestConfig(
            initial_cash=initial_cash,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            stop_loss_pct=stop_loss_pct / 100 if stop_loss_pct else None,
            take_profit_pct=take_profit_pct / 100 if take_profit_pct else None,
            leverage=leverage,
            intraday_strong_close=intraday_strong_close,
            intraday_min_atr_fraction=intraday_min_atr_pct / 100,
            intraday_entry=intraday_entry,
            max_entries_per_day=max_entries_per_day or None,
            max_holding_bars=max_holding_bars or None,
            higher_timeframe_filter=higher_timeframe_filter,
            risk_regime=risk_regime,
            risk_per_trade=risk_per_trade_pct / 100 if risk_per_trade_pct else None,
            max_exposure_fraction=max_exposure_pct / 100,
            exit_mode=exit_mode,
            stop_reentry_mode=stop_reentry_mode,
            trend_entry_buffer=trend_entry_buffer_pct / 100,
            trailing_reentry_mode=trailing_reentry_mode,
            trailing_activation=trailing_activation_pct / 100 if trailing_activation_pct else None,
            trailing_distance=trailing_distance_pct / 100 if trailing_distance_pct else None,
            position_fraction=stored_config.position_fraction if strategy_key else 1.0,
        )
        selected_strategy = make_strategy(
            strategy, config, fast=fast, slow=slow, lookback=lookback,
            momentum_threshold=momentum_threshold, entry_deviation=entry_deviation,
        )
        result = BacktestEngine(config).run(
            signal_candles,
            selected_strategy,
            evaluation_start_ms=since_ms,
        )
        run_repository = BacktestRunRepository(settings.db_path)
        save_result = run_repository.save_with_status(
            result=result,
            candles=candles,
            config=config,
            stage=stage,
            note=note,
            fast_period=fast if strategy == "sma" else None,
            slow_period=slow if strategy == "sma" else None,
            base_run_key=base_run_key or None,
            signal_candles=signal_candles,
            research_plan_id=research_plan_id,
        )
        saved_run = save_result.run
        version = run_repository.get_strategy_version_for_run(saved_run.run_key)
        saved_version = version.version_number if version else None
        advice = analyze_backtest(result, config, research_stage=stage)
    except ValueError as exc:
        return templates.TemplateResponse(
            request=request,
            name="backtest_error.html",
            context={"message": str(exc), "values": values},
            status_code=422,
        )

    metrics = {
        key: value if not isinstance(value, float) or isfinite(value) else None
        for key, value in asdict(result.metrics).items()
    }
    return templates.TemplateResponse(
        request=request,
        name="backtest_result.html",
        context={
            "result": result,
            "annual_performance": annual_performance(result),
            "metrics": metrics,
            "chart_points": _chart_points(result),
            "first_date": _format_date(candles[0].timestamp_ms),
            "last_date": _format_date(candles[-1].timestamp_ms),
            "candle_count": len(candles),
            "warmup_count": len(warmup_candles),
            "warmup_required": warmup_required,
            "values": values,
            "format_date": _format_date,
            "saved_run": saved_run,
            "version_run_count": len(run_repository.list_runs_for_strategy(saved_run.strategy_key, limit=None)),
            "saved_version": saved_version,
            "saved_duplicate": not save_result.created,
            "saved_strategy_created": save_result.strategy_created,
            "advice": advice,
            "advice_url": _advice_url(values, saved_run.run_key, advice) if stage == "development" else None,
        },
    )


def _history_item(
    run: BacktestRun, version_number: int | None = None
) -> dict[str, object]:
    strategy = strategy_family(run.strategy_name)
    policy = json.loads(run.policy_json)
    query: dict[str, str | int | float] = {
        "symbol": run.symbol,
        "timeframe": run.timeframe,
        "strategy": strategy,
        "since": _format_date(run.since_ms),
        "until": _format_date(run.until_ms + TIMEFRAMES_MS[run.timeframe]),
        "initial_cash": run.initial_cash,
        "fee_bps": run.fee_bps,
        "slippage_bps": run.slippage_bps,
        "stop_loss_pct": (run.stop_loss_pct or 0) * 100,
        "take_profit_pct": (run.take_profit_pct or 0) * 100,
        "leverage": run.leverage,
        "stage": run.stage,
        "note": run.note,
        "intraday_strong_close": policy.get("intraday_strong_close", False),
        "intraday_min_atr_pct": policy.get("intraday_min_atr_fraction", 0) * 100,
        "intraday_entry": policy.get("intraday_entry", "breakout"),
        "max_entries_per_day": policy.get("max_entries_per_day") or 0,
        "max_holding_bars": policy.get("max_holding_bars") or 0,
        "higher_timeframe_filter": policy.get("higher_timeframe_filter", False),
        "risk_regime": policy.get("risk_regime", "fixed"),
        "risk_per_trade_pct": (policy.get("risk_per_trade") or 0) * 100,
        "max_exposure_pct": policy.get("max_exposure_fraction", 1) * 100,
        "exit_mode": policy.get("exit_mode", "fixed"),
        "stop_reentry_mode": policy.get("stop_reentry_mode", "immediate"),
        "trend_entry_buffer_pct": policy.get("trend_entry_buffer", 0) * 100,
        "trailing_reentry_mode": policy.get("trailing_reentry_mode", "inherit"),
        "trailing_activation_pct": (policy.get("trailing_activation") or 0) * 100,
        "trailing_distance_pct": (policy.get("trailing_distance") or 0) * 100,
        "research_plan_id": run.research_plan_id,
    }
    if strategy == "momentum":
        _, lookback, threshold = run.strategy_name.split("_")
        query.update(lookback=int(lookback), momentum_threshold=float(threshold))
    elif strategy == "mean-reversion":
        _, _, lookback, deviation = run.strategy_name.split("_")
        query.update(lookback=int(lookback), entry_deviation=float(deviation))
    if run.fast_period is not None and run.slow_period is not None:
        query.update(fast=run.fast_period, slow=run.slow_period)
    edit_query = dict(query)
    edit_query.update(
        base_run_key=run.run_key,
        strategy_key=run.strategy_key or "",
        research_plan_id="", stage="development",
        load_strategy="history",
    )
    return {
        "run": run,
        "replay_url": f"/backtests/run?{urlencode(query)}",
        "result_url": f"/backtests/results/{run.run_key}",
        "matches_url": f"/backtests/results/{run.run_key}/matches",
        "period_since": _format_date(run.since_ms),
        "period_until": _format_date(run.until_ms + TIMEFRAMES_MS[run.timeframe]),
        "parameters": query,
        "edit_url": f"/?{urlencode(edit_query)}#backtest",
        "recorded_date": datetime.fromtimestamp(
            run.created_at_ms / 1000, timezone.utc
        ).date().isoformat(),
        "strategy_key": strategy,
        "strategy_label": {"sma": "SMA 趨勢", "buy-hold": "Buy & Hold", "momentum": "動量", "mean-reversion": "均值回歸", "intraday": "多週期短線"}[strategy],
        "policy": policy,
        "version_number": version_number,
        "created_at": datetime.fromtimestamp(
            run.created_at_ms / 1000, timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC"),
        "stage_label": {
            "development": "Development",
            "validation": "Validation",
            "out_of_sample": "Out-of-Sample",
        }[run.stage],
    }


def _advice_url(
    values: dict[str, object], run_key: str, advice: ResearchAdvice
) -> str | None:
    if not advice.has_candidate:
        return None
    query = dict(values)
    query.update(advice.changes)
    query["base_run_key"] = run_key
    query["load_strategy"] = "advisor"
    return f"/?{urlencode(query)}#backtest"


def _strategy_version_item(
    version: StrategyVersion,
    repository: BacktestRunRepository,
    versions_by_key: dict[str, int],
) -> dict[str, object]:
    labels = {
        "fast_period": "快速均線",
        "slow_period": "慢速均線",
        "stop_loss_pct": "止損",
        "take_profit_pct": "止盈",
        "leverage": "槓桿",
        "policy_json": "資金風險／出場規則",
    }

    def display(field: str, value: object) -> str:
        if field == "policy_json":
            policy = json.loads(str(value))
            risk = policy.get("risk_per_trade")
            sizing = f"單筆資金風險 {risk * 100:.2f}%" if risk is not None else "舊版資金比例倉位"
            mode = "策略訊號出場" if policy.get("exit_mode") == "signal" else "固定止盈＋策略訊號"
            return f"4H方向濾網 {policy.get('higher_timeframe_filter', False)} · {sizing} · 倉位模式 {policy.get('risk_regime', 'fixed')} · 最大曝險 {policy.get('max_exposure_fraction', 1) * 100:.1f}% · {mode} · 追蹤啟動 {(policy.get('trailing_activation') or 0) * 100:.1f}%／距離 {(policy.get('trailing_distance') or 0) * 100:.1f}% · 追蹤後再入 {policy.get('trailing_reentry_mode', 'inherit')} · 趨勢門檻 {policy.get('trend_entry_buffer', 0) * 100:.2f}% · 止損後{'等訊號重置' if policy.get('stop_reentry_mode') == 'signal_reset' else '可重新進場'}"
        if value is None:
            return "未設定"
        if field in {"stop_loss_pct", "take_profit_pct"}:
            return f"{float(value) * 100:.1f}%"
        if field == "leverage":
            return f"{float(value):.1f}x"
        return str(value)

    parent = (
        repository.get_strategy_version(version.previous_strategy_key)
        if version.previous_strategy_key
        else None
    )
    fields = tuple(labels)
    changes = [
        {
            "label": labels[field],
            "before": display(field, getattr(parent, field)),
            "after": display(field, getattr(version, field)),
        }
        for field in fields
        if parent is not None and getattr(parent, field) != getattr(version, field)
    ]
    runs = repository.list_runs_for_strategy(version.strategy_key, limit=None)
    latest_run = runs[0]
    development_run = next((run for run in runs if run.stage == "development"), None)
    selectable_run = development_run or latest_run
    history_item = _history_item(selectable_run, version.version_number)
    development_query = dict(
        symbol=selectable_run.symbol,
        timeframe=selectable_run.timeframe,
        strategy=version.strategy_family,
        since=_format_date(selectable_run.since_ms),
        until=_format_date(
            selectable_run.until_ms + TIMEFRAMES_MS[selectable_run.timeframe]
        ),
        initial_cash=selectable_run.initial_cash,
        fee_bps=selectable_run.fee_bps,
        slippage_bps=selectable_run.slippage_bps,
        stop_loss_pct=(selectable_run.stop_loss_pct or 0) * 100,
        take_profit_pct=(selectable_run.take_profit_pct or 0) * 100,
        leverage=selectable_run.leverage,
        intraday_strong_close=json.loads(selectable_run.policy_json).get("intraday_strong_close", False),
        intraday_min_atr_pct=json.loads(selectable_run.policy_json).get("intraday_min_atr_fraction", 0) * 100,
        intraday_entry=json.loads(selectable_run.policy_json).get("intraday_entry", "breakout"),
        max_entries_per_day=json.loads(selectable_run.policy_json).get("max_entries_per_day") or 0,
        max_holding_bars=json.loads(selectable_run.policy_json).get("max_holding_bars") or 0,
        higher_timeframe_filter=json.loads(selectable_run.policy_json).get("higher_timeframe_filter", False),
        risk_regime=json.loads(selectable_run.policy_json).get("risk_regime", "fixed"),
        risk_per_trade_pct=(json.loads(selectable_run.policy_json).get("risk_per_trade") or 0) * 100,
        max_exposure_pct=json.loads(selectable_run.policy_json).get("max_exposure_fraction", 1) * 100,
        exit_mode=json.loads(selectable_run.policy_json).get("exit_mode", "fixed"),
        stop_reentry_mode=json.loads(selectable_run.policy_json).get("stop_reentry_mode", "immediate"),
        trend_entry_buffer_pct=json.loads(selectable_run.policy_json).get("trend_entry_buffer", 0) * 100,
        trailing_reentry_mode=json.loads(selectable_run.policy_json).get("trailing_reentry_mode", "inherit"),
        trailing_activation_pct=(json.loads(selectable_run.policy_json).get("trailing_activation") or 0) * 100,
        trailing_distance_pct=(json.loads(selectable_run.policy_json).get("trailing_distance") or 0) * 100,
        stage="development",
        note=(
            f"基於 V{version.version_number} 建立 Development 實驗，"
            "請設定 Development 日期"
        ),
        base_run_key=selectable_run.run_key,
        load_strategy="development_branch",
    )
    if version.fast_period is not None and version.slow_period is not None:
        development_query.update(
            fast=version.fast_period,
            slow=version.slow_period,
        )
    if version.strategy_family == "momentum":
        _, lookback, threshold = selectable_run.strategy_name.split("_")
        development_query.update(lookback=int(lookback), momentum_threshold=float(threshold))
    elif version.strategy_family == "mean-reversion":
        _, _, lookback, deviation = selectable_run.strategy_name.split("_")
        development_query.update(lookback=int(lookback), entry_deviation=float(deviation))
    return {
        "version": version,
        "changes": changes,
        "replay_url": history_item["replay_url"],
        "parameters": history_item["parameters"],
        "edit_url": history_item["edit_url"],
        "development_url": f"/?{urlencode(development_query)}#backtest",
        "run_key": selectable_run.run_key,
        "latest_run": latest_run,
        "policy": json.loads(version.policy_json),
        "development_run": development_run,
        "experiment_count": len(runs),
        "experiments": [_history_item(run, version.version_number) for run in runs],
        "parent_version": versions_by_key.get(version.previous_strategy_key or ""),
        "recorded_date": datetime.fromtimestamp(
            version.created_at_ms / 1000, timezone.utc
        ).date().isoformat(),
        "strategy_label": history_item["strategy_label"],
        "created_at": datetime.fromtimestamp(
            version.created_at_ms / 1000, timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC"),
        "latest_stage_label": {
            "development": "Development",
            "validation": "Validation",
            "out_of_sample": "Out-of-Sample",
        }[latest_run.stage],
    }


def _optimization_item(
    item: OptimizationRequest,
    runs: BacktestRunRepository,
) -> dict[str, object]:
    labels = {
        "fast": "快速均線",
        "slow": "慢速均線",
        "stop_loss_pct": "止損 %",
        "take_profit_pct": "止盈 %",
        "leverage": "槓桿",
    }
    base = runs.get_run(item.base_run_key)
    candidate = runs.get_run(item.candidate_run_key) if item.candidate_run_key else None
    base_strategy = runs.get_strategy_version_for_run(item.base_run_key)
    candidate_strategy = (
        runs.get_strategy_version_for_run(item.candidate_run_key)
        if item.candidate_run_key else None
    )
    comparisons = json.loads(item.comparisons_json)
    if base:
        for comparison in comparisons:
            comparison["since_date"] = _format_date(comparison["since_ms"])
            comparison["until_date"] = _format_date(comparison["until_ms"] + TIMEFRAMES_MS[base.timeframe])
    return {
        "request": item,
        "base": base,
        "candidate": candidate,
        "base_version": base_strategy.version_number if base_strategy else None,
        "candidate_version": candidate_strategy.version_number if candidate_strategy else None,
        "requested_at": datetime.fromtimestamp(
            item.requested_at_ms / 1000, timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC"),
        "processed_at": (
            datetime.fromtimestamp(item.processed_at_ms / 1000, timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            )
            if item.processed_at_ms else None
        ),
        "changes": [
            {"label": labels.get(field, field), "value": value}
            for field, value in item.changes.items()
        ],
        "evidence_count": len(item.evidence_run_keys),
        "comparisons": comparisons,
    }

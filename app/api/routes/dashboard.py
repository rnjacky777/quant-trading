from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.backtest.engine import BacktestEngine
from app.backtest.advisor import ResearchAdvice, analyze_backtest
from app.backtest.models import BacktestConfig, BacktestResult
from app.backtest.optimization import (
    OptimizationRequest,
    OptimizationRequestRepository,
)
from app.backtest.runs import (
    BacktestRun,
    BacktestRunRepository,
    StrategyAdjustmentLog,
)
from app.config.settings import Settings
from app.data.downloader import download_candles
from app.data.models import Candle, TIMEFRAMES_MS
from app.data.repository import CandleRepository
from app.exchange.ccxt_client import CcxtHistoricalProvider
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.trend_following import MovingAverageTrendStrategy

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parents[1] / "templates"
)


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
        actual_range = (
            f"{_format_date(candles[0].timestamp_ms)}～"
            f"{_format_date(candles[-1].timestamp_ms)}"
        )
        raise ValueError(
            "選擇區間的 K 線資料不完整："
            f"需要 {expected_count:,} 根，目前只有 {len(candles):,} 根，"
            f"實際覆蓋 {actual_range}。請先下載完整區間"
        )


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    settings = Settings.from_env()
    coverage = CandleRepository(settings.db_path).list_coverage(settings.exchange_id)
    run_repository = BacktestRunRepository(settings.db_path)
    adjustment_logs = run_repository.list_adjustments()
    versions_by_run = {
        log.run_key: log.version_number for log in adjustment_logs
    }
    history = [
        _history_item(run, versions_by_run.get(run.run_key))
        for run in run_repository.list_recent()
    ]
    adjustments = []
    for log in adjustment_logs:
        run = run_repository.get_run(log.run_key)
        if run is not None:
            adjustments.append(
                _adjustment_item(
                    log,
                    run,
                    versions_by_run.get(log.previous_run_key)
                    if log.previous_run_key else None,
                )
            )
    pending_run_keys = {
        item.base_run_key
        for item in OptimizationRequestRepository(settings.db_path).list_requests(
            "pending"
        )
    }
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "coverage": coverage,
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
            "adjustments": adjustments,
            "adjustment_versions": sorted(
                {item["log"].version_number for item in adjustments}
            ),
            "pending_run_keys": pending_run_keys,
        },
    )


@router.get("/strategy-optimizations", response_class=HTMLResponse)
def strategy_optimizations(request: Request) -> HTMLResponse:
    settings = Settings.from_env()
    run_repository = BacktestRunRepository(settings.db_path)
    logs = run_repository.list_adjustments(200)
    versions = {log.run_key: log.version_number for log in logs}
    requests = OptimizationRequestRepository(settings.db_path).list_requests()
    items = [
        _optimization_item(item, run_repository, versions) for item in requests
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


@router.post("/strategy-optimizations/enqueue")
def enqueue_strategy_optimization(
    run_key: str = Form(min_length=64, max_length=64),
    objective: str = Form(default="", max_length=300),
) -> RedirectResponse:
    settings = Settings.from_env()
    run = BacktestRunRepository(settings.db_path).get_run(run_key)
    if run is None:
        return _optimization_redirect("找不到指定的回測版本", "error")
    if run.stage != "development":
        return _optimization_redirect(
            "只有 Development 版本可以標記為策略優化", "error"
        )
    item = OptimizationRequestRepository(settings.db_path).enqueue(run_key, objective)
    return _optimization_redirect(f"已將優化任務 #{item.request_id} 加入佇列")


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
    timeframe: str = Form(pattern=r"^(4h|1d)$"),
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
        count = CandleRepository(settings.db_path).upsert(candles)
        if count == 0:
            return _dashboard_redirect(
                "指定期間沒有可下載的已完成 K 線", "warning", return_to
            )
        return _dashboard_redirect(
            f"已同步 {symbol} {timeframe}，共 {count:,} 根已完成 K 線",
            anchor=return_to,
        )
    except Exception as exc:
        return _dashboard_redirect(f"下載失敗：{exc}", "error", return_to)


@router.post("/data/delete", response_class=HTMLResponse)
def delete_market_data(
    symbol: str = Form(pattern=r"^(BTC|ETH)/USDT$"),
    timeframe: str = Form(pattern=r"^(4h|1d)$"),
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
    timeframe: str = Query(pattern=r"^(4h|1d)$"),
    since: date = Query(),
    until: date = Query(),
    strategy: str = Query(pattern=r"^(sma|buy-hold)$"),
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
    }
    try:
        if until <= since:
            raise ValueError("結束日期必須晚於開始日期")
        if base_run_key and (
            len(base_run_key) != 64
            or any(character not in "0123456789abcdef" for character in base_run_key)
        ):
            raise ValueError("策略基準版本識別碼無效")
        settings = Settings.from_env()
        since_ms, until_ms = _utc_ms(since), _utc_ms(until)
        candles = CandleRepository(settings.db_path).list_range(
            settings.exchange_id, symbol, timeframe, since_ms, until_ms
        )
        _validate_range_coverage(candles, timeframe, since_ms, until_ms)
        selected_strategy = (
            MovingAverageTrendStrategy(fast, slow)
            if strategy == "sma"
            else BuyAndHoldStrategy()
        )
        config = BacktestConfig(
            initial_cash=initial_cash,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            stop_loss_pct=stop_loss_pct / 100 if stop_loss_pct else None,
            take_profit_pct=take_profit_pct / 100 if take_profit_pct else None,
            leverage=leverage,
        )
        result = BacktestEngine(config).run(candles, selected_strategy)
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
        )
        saved_run = save_result.run
        saved_version = next(
            (
                log.version_number
                for log in run_repository.list_adjustments(200)
                if log.run_key == saved_run.run_key
            ),
            None,
        )
        advice = analyze_backtest(result, config)
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
            "metrics": metrics,
            "chart_points": _chart_points(result),
            "first_date": _format_date(candles[0].timestamp_ms),
            "last_date": _format_date(candles[-1].timestamp_ms),
            "candle_count": len(candles),
            "values": values,
            "format_date": _format_date,
            "saved_run": saved_run,
            "saved_version": saved_version,
            "saved_duplicate": not save_result.created,
            "advice": advice,
            "advice_url": _advice_url(values, saved_run.run_key, advice),
        },
    )


def _history_item(
    run: BacktestRun, version_number: int | None = None
) -> dict[str, object]:
    strategy = "sma" if run.fast_period is not None else "buy-hold"
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
    }
    if run.fast_period is not None and run.slow_period is not None:
        query.update(fast=run.fast_period, slow=run.slow_period)
    edit_query = dict(query)
    edit_query.update(
        base_run_key=run.run_key,
        load_strategy="history",
    )
    return {
        "run": run,
        "replay_url": f"/backtests/run?{urlencode(query)}",
        "edit_url": f"/?{urlencode(edit_query)}#backtest",
        "recorded_date": datetime.fromtimestamp(
            run.created_at_ms / 1000, timezone.utc
        ).date().isoformat(),
        "strategy_key": strategy,
        "strategy_label": "SMA 趨勢" if strategy == "sma" else "Buy & Hold",
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


def _adjustment_item(
    log: StrategyAdjustmentLog,
    run: BacktestRun,
    parent_version: int | None,
) -> dict[str, object]:
    labels = {
        "since_ms": "開始日期",
        "until_ms": "結束日期",
        "fast_period": "快速均線",
        "slow_period": "慢速均線",
        "initial_cash": "初始資金",
        "fee_bps": "手續費 bps",
        "slippage_bps": "滑價 bps",
        "stop_loss_pct": "止損",
        "take_profit_pct": "止盈",
        "leverage": "槓桿",
        "stage": "研究階段",
        "data_fingerprint": "市場資料版本",
    }

    def display(field: str, value: object) -> str:
        if value is None:
            return "未設定"
        if field in {"since_ms", "until_ms"}:
            return _format_date(int(value))
        if field in {"stop_loss_pct", "take_profit_pct"}:
            return f"{float(value) * 100:.1f}%"
        if field == "leverage":
            return f"{float(value):.1f}x"
        if field == "data_fingerprint":
            return str(value)[:8]
        return str(value)

    changes = [
        {
            "label": labels.get(field, field),
            "before": display(field, values["from"]),
            "after": display(field, values["to"]),
        }
        for field, values in log.changes.items()
    ]
    history_item = _history_item(run)
    development_query = dict(
        symbol=run.symbol,
        timeframe=run.timeframe,
        strategy=log.strategy_family,
        since=_format_date(run.since_ms),
        until=_format_date(run.until_ms + TIMEFRAMES_MS[run.timeframe]),
        initial_cash=run.initial_cash,
        fee_bps=run.fee_bps,
        slippage_bps=run.slippage_bps,
        stop_loss_pct=(run.stop_loss_pct or 0) * 100,
        take_profit_pct=(run.take_profit_pct or 0) * 100,
        leverage=run.leverage,
        stage="development",
        note=f"基於 V{log.version_number} 建立 Development 分支，請設定 Development 日期",
        base_run_key=run.run_key,
        load_strategy="development_branch",
    )
    if run.fast_period is not None and run.slow_period is not None:
        development_query.update(fast=run.fast_period, slow=run.slow_period)
    return {
        "log": log,
        "changes": changes,
        "replay_url": history_item["replay_url"],
        "edit_url": history_item["edit_url"],
        "development_url": f"/?{urlencode(development_query)}#backtest",
        "parent_version": parent_version,
        "recorded_date": datetime.fromtimestamp(
            log.created_at_ms / 1000, timezone.utc
        ).date().isoformat(),
        "strategy_label": (
            "SMA 趨勢" if log.strategy_family == "sma" else "Buy & Hold"
        ),
        "created_at": datetime.fromtimestamp(
            log.created_at_ms / 1000, timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC"),
        "stage_label": {
            "development": "Development",
            "validation": "Validation",
            "out_of_sample": "Out-of-Sample",
        }[log.stage],
    }


def _optimization_item(
    item: OptimizationRequest,
    runs: BacktestRunRepository,
    versions: dict[str, int],
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
    return {
        "request": item,
        "base": base,
        "candidate": candidate,
        "base_version": versions.get(item.base_run_key),
        "candidate_version": versions.get(item.candidate_run_key or ""),
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
    }

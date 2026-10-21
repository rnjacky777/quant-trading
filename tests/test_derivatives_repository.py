from app.data.derivatives_repository import DerivativesRepository
from app.data.models import FundingRate, MarkPriceCandle
from app.risk.margin import MarginBracket


def test_derivatives_inputs_round_trip_through_sqlite(tmp_path) -> None:
    repository = DerivativesRepository(tmp_path / "market.sqlite3")
    funding = FundingRate("binanceusdm", "BTC/USDT", 1000, 0.0001, 100_000)
    mark = MarkPriceCandle(
        "binanceusdm", "BTC/USDT", 1000, 100, 101, 99, 100, "1m"
    )
    brackets = [
        MarginBracket(0, 10_000, 0.005, 0),
        MarginBracket(10_000, 50_000, 0.01, 50),
    ]

    assert repository.upsert_funding_rates([funding]) == 1
    assert repository.upsert_mark_prices([mark]) == 1
    assert repository.save_margin_brackets(
        "binanceusdm", "BTC/USDT", 500, brackets
    ) == 2

    assert repository.list_funding_rates(
        "binanceusdm", "BTC/USDT", 0, 2000
    ) == [funding]
    assert repository.list_mark_prices(
        "binanceusdm", "BTC/USDT", "1m", 0, 2000
    ) == [mark]
    effective_at, model = repository.latest_margin_model(
        "binanceusdm", "BTC/USDT", 1000
    )
    assert effective_at == 500
    assert model.maintenance_margin(200, 100) == 150

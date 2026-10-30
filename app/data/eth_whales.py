"""Read-only Ethereum large-transfer monitor: native ETH and USDT/USDC transfers above a threshold.

Uses a public JSON-RPC endpoint (no keys, never signs or sends transactions). Each confirmed block is
scanned once; alerts are appended to a JSONL log with the block time, building point-in-time data for
later research. Not a trading signal: nothing here is tested as predictive.
"""
from dataclasses import asdict, dataclass
import json
import time
from pathlib import Path
from typing import Callable, Protocol
from urllib.request import Request, urlopen

DEFAULT_RPC = "https://ethereum-rpc.publicnode.com"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
# Mainnet token contracts (lower-case) and their decimals.
STABLECOINS = {"0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT", 6),
               "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC", 6)}
CONFIRMATIONS = 2


class RpcError(RuntimeError):
    pass


class Rpc(Protocol):
    def call(self, method: str, params: list): ...


class HttpRpc:
    def __init__(self, url: str = DEFAULT_RPC, timeout: float = 15, attempts: int = 3) -> None:
        self.url, self.timeout, self.attempts = url, timeout, attempts

    def call(self, method: str, params: list):
        body = json.dumps(dict(jsonrpc="2.0", id=1, method=method, params=params)).encode()
        error: Exception | None = None
        for attempt in range(self.attempts):
            try:
                request = Request(self.url, body, {"Content-Type": "application/json", "User-Agent": "quant-trading-monitor"})
                with urlopen(request, timeout=self.timeout) as response:
                    reply = json.loads(response.read())
                if "error" in reply:
                    raise RpcError(f"{method}: {reply['error']}")
                return reply["result"]
            except (OSError, ValueError, RpcError) as exc:
                error = exc
                time.sleep(min(2 ** attempt, 4))
        raise RpcError(f"{method} failed after {self.attempts} attempts: {error}")


@dataclass(frozen=True)
class WhaleTransfer:
    block: int
    block_time: int
    tx_hash: str
    asset: str
    amount: float
    usd: float
    sender: str
    receiver: str
    sender_label: str | None = None
    receiver_label: str | None = None


def address_from_topic(topic: str) -> str:
    return "0x" + topic[-40:].lower()


def scan_block(rpc: Rpc, number: int, *, min_eth: float, min_usd: float, eth_usd: float,
               labels: dict[str, str]) -> list[WhaleTransfer]:
    """Large native ETH and stablecoin transfers in one block."""
    block = rpc.call("eth_getBlockByNumber", [hex(number), True])
    when = int(block["timestamp"], 16)
    out = []

    def make(tx_hash: str, asset: str, amount: float, usd: float, sender: str, receiver: str) -> WhaleTransfer:
        return WhaleTransfer(number, when, tx_hash, asset, amount, usd, sender, receiver,
                             labels.get(sender), labels.get(receiver))
    for tx in block["transactions"]:
        eth = int(tx["value"], 16) / 1e18
        if eth >= min_eth and tx.get("to"):
            out.append(make(tx["hash"], "ETH", eth, eth * eth_usd, tx["from"].lower(), tx["to"].lower()))
    logs = rpc.call("eth_getLogs", [dict(fromBlock=hex(number), toBlock=hex(number),
                                          address=list(STABLECOINS), topics=[TRANSFER_TOPIC])])
    for log in logs:
        token = STABLECOINS.get(log["address"].lower())
        if token is None or len(log["topics"]) < 3:
            continue
        symbol, decimals = token
        amount = int(log["data"], 16) / 10 ** decimals
        if amount >= min_usd:
            out.append(make(log["transactionHash"], symbol, amount, amount,
                            address_from_topic(log["topics"][1]), address_from_topic(log["topics"][2])))
    return out


class WhaleWatcher:
    """Scans each confirmed block once; resumes from its state file after a restart."""

    def __init__(self, rpc: Rpc, root: Path, eth_usd: Callable[[], float], *, min_eth: float = 1000,
                 min_usd: float = 5_000_000, labels: dict[str, str] | None = None) -> None:
        self.rpc, self.root, self.eth_usd = rpc, root, eth_usd
        self.min_eth, self.min_usd, self.labels = min_eth, min_usd, {k.lower(): v for k, v in (labels or {}).items()}
        self.state = root / "state.json"
        self.log = root / "transfers.jsonl"

    def last_scanned(self) -> int | None:
        return json.loads(self.state.read_text(encoding="utf-8"))["last_block"] if self.state.exists() else None

    def step(self, max_blocks: int = 20) -> list[WhaleTransfer]:
        head = int(self.rpc.call("eth_blockNumber", []), 16) - CONFIRMATIONS
        last = self.last_scanned()
        start = head if last is None else last + 1
        found = []
        price = self.eth_usd()
        for number in range(start, min(head, start + max_blocks - 1) + 1):
            batch = scan_block(self.rpc, number, min_eth=self.min_eth, min_usd=self.min_usd, eth_usd=price, labels=self.labels)
            self.root.mkdir(parents=True, exist_ok=True)
            with self.log.open("a", encoding="utf-8") as handle:
                for transfer in batch:
                    handle.write(json.dumps(dict(asdict(transfer), eth_usd=price, recorded_ms=int(time.time() * 1000))) + "\n")
            self.state.write_text(json.dumps(dict(last_block=number)), encoding="utf-8")
            found += batch
        return found

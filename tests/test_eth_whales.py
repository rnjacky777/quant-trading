from app.data.eth_whales import TRANSFER_TOPIC, WhaleWatcher, scan_block

USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"


def topic(address):
    return "0x" + "0" * 24 + address[2:]


class FakeRpc:
    def __init__(self, head=105):
        self.head, self.calls = head, []

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_blockNumber":
            return hex(self.head)
        if method == "eth_getBlockByNumber":
            n = int(params[0], 16)
            return dict(timestamp=hex(1_700_000_000 + n), transactions=[
                dict(hash=f"0xbig{n}", value=hex(2000 * 10 ** 18), to="0xBBB", **{"from": "0xAAA"}),
                dict(hash=f"0xsmall{n}", value=hex(5 * 10 ** 18), to="0xccc", **{"from": "0xddd"}),
                dict(hash=f"0xdeploy{n}", value=hex(5000 * 10 ** 18), to=None, **{"from": "0xeee"})])
        if method == "eth_getLogs":
            return [dict(address=USDT.upper().replace("0X", "0x"), transactionHash="0xusdt",
                         topics=[TRANSFER_TOPIC, topic("0x" + "1" * 40), topic("0x" + "2" * 40)], data=hex(8_000_000 * 10 ** 6)),
                    dict(address=USDT, transactionHash="0xtiny",
                         topics=[TRANSFER_TOPIC, topic("0x" + "3" * 40), topic("0x" + "4" * 40)], data=hex(10 * 10 ** 6))]
        raise AssertionError(method)


def test_scan_keeps_large_eth_and_stablecoin_transfers_with_labels():
    found = scan_block(FakeRpc(), 100, min_eth=1000, min_usd=5_000_000, eth_usd=3000, labels={"0xbbb": "exchange-x"})
    assert [(t.asset, t.amount) for t in found] == [("ETH", 2000), ("USDT", 8_000_000)]
    eth = found[0]
    assert eth.usd == 6_000_000 and eth.receiver_label == "exchange-x" and eth.sender == "0xaaa"
    assert found[1].sender == "0x" + "1" * 40 and found[1].block_time == 1_700_000_100


def test_watcher_scans_confirmed_blocks_once_and_resumes(tmp_path):
    rpc = FakeRpc(head=105)
    w = WhaleWatcher(rpc, tmp_path, lambda: 3000.0)
    first = w.step()
    assert w.last_scanned() == 103 and len(first) == 2  # starts at head minus confirmations
    rpc.head = 108
    again = WhaleWatcher(rpc, tmp_path, lambda: 3000.0).step()
    assert w.last_scanned() == 106 and {t.block for t in again} == {104, 105, 106}
    lines = (tmp_path / "transfers.jsonl").read_text().splitlines()
    assert len(lines) == 8

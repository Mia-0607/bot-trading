"""Pruebas locales sin red ni inferencia del LLM."""
import copy
import unittest

from core import DAY_MS, closed_candles, features, number, paper_step, proposal

BASE = 1_728_000_000_000


def candles(count=22):
    return [[BASE + i * DAY_MS, "100", "100", "100", "100", "1",
             BASE + (i + 1) * DAY_MS] for i in range(count)]


def account():
    return {"cash": 50000.0, "qty": 0.0, "equity": 50000.0,
            "day_start": 50000.0, "risk_day": "", "risk_blocked": False}


class CoreTests(unittest.TestCase):
    def test_open_candle_is_excluded(self):
        rows = closed_candles(candles(), BASE + 21 * DAY_MS + 1000, 48)
        self.assertEqual(len(rows), 21)

    def test_last_closed_candle_is_not_blindly_dropped(self):
        rows = closed_candles(candles(21), BASE + 21 * DAY_MS + 1000, 48)
        self.assertEqual(len(rows), 21)

    def test_empty_data(self):
        with self.assertRaises(ValueError):
            closed_candles([], BASE, 48)

    def test_duplicate_dates(self):
        rows = candles()
        rows[10] = rows[9]
        with self.assertRaises(ValueError):
            closed_candles(rows, BASE + 22 * DAY_MS + 1, 48)

    def test_missing_day(self):
        rows = candles(23)
        del rows[10]
        with self.assertRaises(ValueError):
            closed_candles(rows, BASE + 23 * DAY_MS + 1, 48)

    def test_bad_price(self):
        for value in ["nan", "inf", "0", "-1", "abc"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                rows = candles()
                rows[5][4] = value
                closed_candles(rows, BASE + 22 * DAY_MS + 1, 48)

    def test_bad_dimensions(self):
        with self.assertRaises(ValueError):
            closed_candles([[BASE]], BASE, 48)

    def test_insufficient_history(self):
        with self.assertRaises(ValueError):
            closed_candles(candles(20), BASE + 20 * DAY_MS + 1, 48)

    def test_stale_data(self):
        with self.assertRaises(ValueError):
            closed_candles(candles(), BASE + 25 * DAY_MS, 48)

    def test_constant_series_indicators(self):
        result = features(candles())
        self.assertEqual(result, {"close": 100, "ret_1d": 0, "dist_sma20": 0, "vol20": 0})

    def test_configuration_limits(self):
        for value in ["nan", "inf", "-0.5", "0", "1.1"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value, "límite", maximum=1, strict_min=True)

    def test_llm_contract(self):
        data = {"action": "buy", "symbol": "BTCUSDT", "candle_ts": BASE, "reason": "Señal de ejemplo"}
        self.assertEqual(proposal(data, "BTCUSDT", BASE)["action"], "buy")
        for key, value in [("action", []), ("symbol", "ETHUSDT"), ("candle_ts", str(BASE)), ("reason", 42)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                proposal({**data, key: value}, "BTCUSDT", BASE)

    def test_buy_respects_cash_and_exposure(self):
        original = account()
        result, action, _ = paper_step(original, "buy", 100, BASE, .5, .03)
        self.assertEqual((result["cash"], result["qty"], result["equity"], action), (25000, 250, 50000, "buy"))
        self.assertEqual(original, account())

    def test_no_second_buy_or_short_sale(self):
        result, _, _ = paper_step(account(), "buy", 100, BASE, .5, .03)
        second, action, _ = paper_step(result, "buy", 100, BASE, .5, .03)
        self.assertEqual(action, "hold")
        self.assertEqual(second["cash"], 25000)
        _, action, _ = paper_step(account(), "sell", 100, BASE, .5, .03)
        self.assertEqual(action, "hold")

    def test_loss_limit_blocks_at_threshold_and_stays_latched(self):
        current, _, _ = paper_step(account(), "buy", 100, BASE, .5, .03)
        blocked, action, _ = paper_step(current, "sell", 94, BASE + 1000, .5, .03)
        self.assertTrue(blocked["risk_blocked"])
        self.assertEqual(action, "hold")
        recovered, action, _ = paper_step(blocked, "sell", 100, BASE + 2000, .5, .03)
        self.assertTrue(recovered["risk_blocked"])
        self.assertEqual(action, "hold")

    def test_daily_base_rolls_forward(self):
        current, _, _ = paper_step(account(), "buy", 100, BASE, .5, .03)
        current["equity"] = 52000
        current["risk_blocked"] = True
        result, _, _ = paper_step(current, "hold", 108, BASE + DAY_MS, .5, .03)
        self.assertEqual(result["day_start"], 52000)
        self.assertFalse(result["risk_blocked"])

    def test_sell_updates_equity(self):
        current, _, _ = paper_step(account(), "buy", 100, BASE, .5, .03)
        result, action, _ = paper_step(current, "sell", 110, BASE + 1000, .5, .03)
        self.assertEqual((result["cash"], result["qty"], result["equity"], action), (52500, 0, 52500, "sell"))


if __name__ == "__main__":
    unittest.main()

"""Pruebas del backend con dependencias instaladas y servicios externos simulados."""
import asyncio
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

READY = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx", "dotenv"))
if READY:
    import httpx
    import main
from test_core import BASE, candles
from core import DAY_MS


@unittest.skipUnless(READY, "Requiere las dependencias de backend/requirements.txt")
class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = patch.multiple(main, DB_PATH=Path(self.temp.name) / "test.db", OPERATOR_KEY="test-only-key")
        self.settings.start()

        async def idle():
            await asyncio.Event().wait()

        self.background = patch.object(main, "loop", idle)
        self.background.start()
        self.context = main.lifespan(main.app)
        await self.context.__aenter__()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test")
        self.headers = {"X-API-Key": "test-only-key"}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.context.__aexit__(None, None, None)
        self.background.stop()
        self.settings.stop()
        self.temp.cleanup()

    async def test_state_and_controls_require_auth(self):
        self.assertEqual((await self.client.get("/api/state")).status_code, 401)
        self.assertEqual((await self.client.post("/api/start", headers={"X-API-Key": "wrong"})).status_code, 401)
        self.assertEqual((await self.client.get("/api/state", headers=self.headers)).status_code, 200)

    async def test_stop_during_llm_prevents_operation(self):
        async def delayed(*args):
            await main.control("stop")
            return {"action": "buy", "reason": "Prueba"}
        await main.control("start")
        with patch.object(main, "klines", AsyncMock(return_value=candles())), patch.object(main, "ask_llm", delayed):
            await main.cycle()
        self.assertEqual(main.account()["cash"], 50000)
        self.assertEqual(main.db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], 0)

    async def test_stop_then_restart_invalidates_inflight_cycle(self):
        async def delayed(*args):
            await main.control("stop")
            await main.control("start")
            return {"action": "buy", "reason": "Prueba"}
        await main.control("start")
        with patch.object(main, "klines", AsyncMock(return_value=candles())), patch.object(main, "ask_llm", delayed):
            await main.cycle()
        self.assertEqual(main.db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], 0)

    async def test_duplicate_and_restart_preserve_account(self):
        await main.control("start")
        with patch.object(main, "klines", AsyncMock(return_value=candles())), \
                patch.object(main, "ask_llm", AsyncMock(return_value={"action": "buy", "reason": "Prueba"})), \
                patch.object(main, "now_ms", return_value=BASE + 22 * DAY_MS + 1000):
            await main.cycle()
            await main.cycle()
        before = main.account()
        self.assertEqual(before["equity"], 50000)
        self.assertEqual(before["qty"], 250)
        self.assertEqual(main.db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], 1)
        await self.context.__aexit__(None, None, None)
        self.context = main.lifespan(main.app)
        await self.context.__aenter__()
        self.assertEqual(main.account(), before)
        self.assertEqual(main.STATUS, "stopped")

    async def test_failed_commit_rolls_back_everything(self):
        main.db.execute("CREATE TRIGGER reject_account BEFORE INSERT ON accounts BEGIN SELECT RAISE(ABORT, 'test'); END")
        await main.control("start")
        with patch.object(main, "klines", AsyncMock(return_value=candles())), \
                patch.object(main, "ask_llm", AsyncMock(return_value={"action": "buy", "reason": "Prueba"})), \
                patch.object(main, "now_ms", return_value=BASE + 22 * DAY_MS + 1000):
            with self.assertRaises(main.sqlite3.IntegrityError):
                await main.cycle()
        self.assertEqual(main.account()["cash"], 50000)
        self.assertEqual(main.db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], 0)

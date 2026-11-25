import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import httpx
from fastapi.testclient import TestClient
import main


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.key = patch.object(main, 'OPERATOR_KEY', 'test-only-operator-key-123456789')
        self.path = patch.object(main, 'DB_PATH', Path(self.temp.name) / 'test.db')
        self.key.start(); self.path.start()
        self.client = TestClient(main.app).__enter__()
        self.headers = {'X-API-Key': main.OPERATOR_KEY}
        self.market = patch.object(main, 'public_get', AsyncMock(return_value={'symbol':'BTCUSDT', 'price':'50000'}))
        self.market.start()

    def tearDown(self):
        self.market.stop()
        self.client.__exit__(None, None, None)
        self.key.stop(); self.path.stop(); self.temp.cleanup()

    def order(self, side='buy', amount='1000', rid=None, **extra):
        return self.client.post('/api/trades', headers=self.headers,
            json=dict(request_id=rid or str(uuid4()), side=side, amount=amount, **extra))

    def test_auth_all_routes(self):
        for route in ['/api/state','/api/candles','/api/history']:
            self.assertEqual(self.client.get(route).status_code, 401)
        self.assertEqual(self.client.post('/api/trades', json={}).status_code, 401)
        self.assertEqual(self.client.get('/api/state', headers={'X-API-Key':'wrong'}).status_code, 401)

    def test_buy_sell_persistence_and_idempotency(self):
        rid = str(uuid4())
        first = self.order(rid=rid)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()['qty'], '0.02000000')
        self.assertEqual(self.order(rid=rid).json(), first.json())
        self.assertEqual(self.order(amount='1001', rid=rid).status_code, 409)
        main.public_get.return_value = {'symbol':'BTCUSDT','price':'60000'}
        sale = self.order('sell', '0.02')
        self.assertEqual(sale.status_code, 200)
        self.assertEqual(float(sale.json()['cash']), 50200)
        self.client.__exit__(None, None, None)
        self.client = TestClient(main.app).__enter__()
        state = self.client.get('/api/state', headers=self.headers).json()
        self.assertEqual(float(state['cash']), 50200)
        self.assertEqual(float(state['qty']), 0)
        self.assertEqual(len(state['history']), 2)

    def test_validation_and_insufficient_balance(self):
        for amount in ['0','-1','NaN','Infinity','1e3','0.000000001',True,1000]:
            self.assertIn(self.order(amount=amount).status_code, [409,422])
        self.assertEqual(self.order(amount='50001').status_code, 409)
        self.assertEqual(self.order('sell','1').status_code, 409)
        self.assertEqual(self.order(price='1').status_code, 422)
        self.assertEqual(self.order('hold').status_code, 422)
        self.assertEqual(self.client.get('/api/history?limit=501', headers=self.headers).status_code, 422)
        self.assertEqual(self.client.get('/api/history', headers=self.headers).json()['history'], [])

    def test_outage_no_trade_but_account_readable(self):
        main.public_get.side_effect = httpx.ConnectError('private external details')
        r = self.order()
        self.assertEqual(r.status_code, 503)
        self.assertNotIn('private external', r.text)
        state = self.client.get('/api/state', headers=self.headers).json()
        self.assertIsNone(state['equity']); self.assertIsNone(state['quote'])
        self.assertEqual(float(state['cash']), 50000)
        self.assertEqual(state['history'], [])

    def test_invalid_market_prices(self):
        for p in ['0','-1','NaN','Infinity']:
            main.public_get.return_value = {'symbol':'BTCUSDT','price':p}
            self.assertEqual(self.order().status_code, 503)
        main.public_get.return_value = {'symbol':'ETHUSDT','price':'1'}
        self.assertEqual(self.order().status_code, 503)

    def test_expired_quote(self):
        old = {'price':'50000', 'requested_at':main.now_ms()-11000, 'received_at':main.now_ms()}
        with patch.object(main, 'quote', AsyncMock(return_value=old)):
            self.assertEqual(self.order().status_code, 409)
        self.assertEqual(self.client.get('/api/history', headers=self.headers).json()['history'], [])

    def test_candles_validation(self):
        ts = main.now_ms() // 60000 * 60000
        rows = [[ts-60000,'10','12','9','11','1',ts-1], [ts,'11','12','9','10','1',ts+59999]]
        main.public_get.return_value = rows
        self.assertEqual(self.client.get('/api/candles', headers=self.headers).status_code, 200)
        rows[1][2] = '8'
        self.assertEqual(self.client.get('/api/candles', headers=self.headers).status_code, 503)

    def test_no_legacy_automation_endpoint(self):
        self.assertEqual(self.client.post('/api/start', headers=self.headers).status_code, 404)


if __name__ == '__main__':
    unittest.main()

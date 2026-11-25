import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from paper import Store


class PaperTests(unittest.TestCase):
    def test_rounding_and_full_sale(self):
        s = Store(':memory:')
        try:
            quote = {'price':'30000.12345678', 'requested_at':1000, 'received_at':1001}
            bought = s.trade('a','buy','1000',quote,lambda:1002)
            self.assertLessEqual(Decimal(bought['total']), Decimal('1000'))
            self.assertEqual(sum((Decimal(bought['cash']), Decimal(bought['total']))), Decimal('50000'))
            s.trade('b','sell',bought['qty'],quote,lambda:1002)
            self.assertEqual(s.account(), (Decimal('50000'),Decimal('0')))
        finally:
            s.db.close()

    def test_failure_rolls_back_both_balances_and_history(self):
        s = Store(':memory:')
        try:
            s.db.execute("CREATE TRIGGER fail_trade BEFORE INSERT ON paper_trades BEGIN SELECT RAISE(ABORT,'test'); END")
            with self.assertRaises(Exception):
                s.trade('a','buy','1000', {'price':'50000','requested_at':1,'received_at':2},lambda:3)
            self.assertEqual(s.account(), (Decimal('50000'),Decimal('0')))
            self.assertEqual(s.history(), [])
        finally:
            s.db.close()

    def test_concurrent_spending_cannot_overdraw(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'paper.db'
            s = Store(path); s.db.close()
            def buy(rid):
                store = Store(path)
                try:
                    store.trade(rid,'buy','40000', {'price':'50000','requested_at':1,'received_at':2}, lambda:3)
                    return True
                except ValueError:
                    return False
                finally:
                    store.db.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                self.assertEqual(sum(pool.map(buy, ['a','b'])), 1)
            s = Store(path)
            self.assertEqual(s.account()[0], Decimal('10000'))
            self.assertEqual(len(s.history()), 1)
            s.db.close()

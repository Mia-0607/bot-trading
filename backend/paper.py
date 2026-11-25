"""Contabilidad decimal y persistencia transaccional SOLO simulada."""
import json
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_DOWN

STEP = Decimal('0.00000001')


def decimal(value):
    if isinstance(value, bool):
        raise ValueError('Cantidad inválida')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('Cantidad inválida') from None
    if not result.is_finite() or result <= 0 or result > Decimal('1000000000'):
        raise ValueError('Cantidad fuera de rango')
    return result


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=5)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS paper_account(
            id INTEGER PRIMARY KEY CHECK(id=1), cash TEXT NOT NULL, qty TEXT NOT NULL);
          INSERT OR IGNORE INTO paper_account VALUES(1,'50000','0');
          CREATE TABLE IF NOT EXISTS paper_trades(
            id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT UNIQUE NOT NULL,
            fingerprint TEXT NOT NULL, payload TEXT NOT NULL);
        ''')

    def account(self):
        cash, qty = self.db.execute('SELECT cash,qty FROM paper_account WHERE id=1').fetchone()
        return Decimal(cash), Decimal(qty)

    def history(self, limit=100, offset=0):
        return [json.loads(r[0]) for r in self.db.execute(
            'SELECT payload FROM paper_trades ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))]

    def existing(self, request_id, fingerprint):
        row = self.db.execute('SELECT fingerprint,payload FROM paper_trades WHERE request_id=?', (request_id,)).fetchone()
        if row:
            if row[0] != fingerprint:
                raise ValueError('Identificador ya utilizado con otra operación')
            return json.loads(row[1])

    def trade(self, request_id, side, amount, quote, now):
        amount = decimal(amount)
        fingerprint = f'{side}:{amount.normalize()}'
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.existing(request_id, fingerprint)
            if old:
                return old
            if not 0 <= now() - quote['requested_at'] <= 10000:
                raise ValueError('Precio vencido; consulta nuevamente')
            price = decimal(quote['price'])
            cash, qty = self.account()
            if side == 'buy':
                if amount > cash:
                    raise ValueError('Saldo USDT insuficiente')
                units = (amount / price).quantize(STEP, rounding=ROUND_DOWN)
            elif side == 'sell':
                units = amount
                if units != units.quantize(STEP):
                    raise ValueError('Máximo 8 decimales para BTC')
                if units > qty:
                    raise ValueError('Saldo BTC insuficiente')
            else:
                raise ValueError('Acción inválida')
            if units <= 0:
                raise ValueError('Importe demasiado pequeño')
            total = units * price
            cash += -total if side == 'buy' else total
            qty += units if side == 'buy' else -units
            record = dict(request_id=request_id, side=side, symbol='BTCUSDT',
                          amount=str(amount), price=str(price), qty=str(units), total=str(total),
                          cash=str(cash), position=str(qty), equity=str(cash + qty * price),
                          recorded_at=now(), quote_requested_at=quote['requested_at'],
                          quote_received_at=quote['received_at'], fee='0', mode='paper',
                          execution_model='fresh_public_ticker')
            self.db.execute('UPDATE paper_account SET cash=?,qty=? WHERE id=1', (str(cash), str(qty)))
            self.db.execute('INSERT INTO paper_trades(request_id,fingerprint,payload) VALUES(?,?,?)',
                            (request_id, fingerprint, json.dumps(record)))
            return record

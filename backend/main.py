"""V0.2: mercado público MEXC y operaciones manuales SOLO simuladas."""
import hmac
import os
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import UUID
import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from paper import Store, decimal

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
OPERATOR_KEY = os.getenv('OPERATOR_API_KEY', '')
DB_PATH = Path(os.getenv('DB_PATH', str(ROOT / 'bot-v02.db')))
db = None


def now_ms():
    return time.time_ns() // 1_000_000


async def public_get(path, params=None):
    # URL fija, solo GET público. Sin claves MEXC ni endpoints de órdenes.
    async with httpx.AsyncClient(timeout=6, trust_env=False, follow_redirects=False) as client:
        r = await client.get('https://api.mexc.com/api/v3/' + path, params=params,
                             headers={'Cache-Control': 'no-cache'})
        r.raise_for_status()
        return r.json()


async def quote():
    start = now_ms()
    data = await public_get('ticker/price', {'symbol': 'BTCUSDT'})
    received = now_ms()
    if data['symbol'] != 'BTCUSDT' or not 0 <= received - start <= 10000:
        raise ValueError('Cotización inválida o vencida')
    return {'price': str(decimal(data['price'])), 'requested_at': start, 'received_at': received,
            'expires_at': start + 10000}


async def candles():
    rows = await public_get('klines', {'symbol': 'BTCUSDT', 'interval': '1m', 'limit': 60})
    if not isinstance(rows, list) or not 2 <= len(rows) <= 60:
        raise ValueError('Velas inválidas')
    result = []
    for row in rows:
        ts, end = int(row[0]), int(row[6])
        o, h, low, c = [decimal(row[i]) for i in (1, 2, 3, 4)]
        if low > min(o, c) or h < max(o, c) or ts > now_ms() + 5000 or not ts < end <= ts + 60000:
            raise ValueError('Vela inválida')
        if result and ts != result[-1]['ts'] + 60000:
            raise ValueError('Velas desordenadas o incompletas')
        result.append(dict(ts=ts, end=end, open=str(o), high=str(h), low=str(low), close=str(c)))
    if now_ms() - result[-1]['ts'] > 120000:
        raise ValueError('Velas vencidas')
    return result


@asynccontextmanager
async def lifespan(app):
    global db
    if len(OPERATOR_KEY.strip()) < 24:
        raise RuntimeError('Configura OPERATOR_API_KEY con al menos 24 caracteres en backend/.env')
    db = Store(DB_PATH)
    try:
        yield
    finally:
        db.db.close()


async def auth(x_api_key: str = Header(default='')):
    if not OPERATOR_KEY or not hmac.compare_digest(x_api_key.encode(), OPERATOR_KEY.encode()):
        raise HTTPException(401, 'Credencial del operador ausente o incorrecta')


app = FastAPI(title='Bot Trading V0.2 · SOLO SIMULACIÓN', version='0.2.0', lifespan=lifespan)


@app.middleware('http')
async def no_cache(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.exception_handler(sqlite3.Error)
async def storage_error(request: Request, error):
    return JSONResponse(status_code=503, content={'detail': 'Persistencia no disponible. No se confirmó la operación.'})


async def market_call(fn):
    try:
        return await fn()
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, ArithmeticError):
        raise HTTPException(503, 'MEXC no disponible o datos inválidos. No se ejecutó una operación nueva.') from None


@app.get('/api/state', dependencies=[Depends(auth)])
async def state():
    market, error = None, None
    try:
        market = await market_call(quote)
    except HTTPException as exc:
        error = exc.detail
    cash, qty = db.account()
    return dict(symbol='BTCUSDT', mode='paper', capital='50000', cash=str(cash), qty=str(qty),
                equity=str(cash + qty * decimal(market['price'])) if market else None,
                quote=market, market_error=error, history=db.history(), server_time=now_ms())


@app.get('/api/candles', dependencies=[Depends(auth)])
async def get_candles():
    return {'symbol': 'BTCUSDT', 'interval': '1m', 'candles': await market_call(candles)}


@app.get('/api/history', dependencies=[Depends(auth)])
async def history(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return {'history': db.history(limit, offset)}


class Order(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    side: Literal['buy', 'sell']
    amount: str = Field(min_length=1, max_length=32, pattern=r'^\d+(\.\d{1,8})?$')


@app.post('/api/trades', dependencies=[Depends(auth)])
async def trade(order: Order):
    try:
        amount = decimal(order.amount)
        old = db.existing(str(order.request_id), f'{order.side}:{amount.normalize()}')
        if old:
            return old
        fresh = await market_call(quote)
        return db.trade(str(order.request_id), order.side, amount, fresh, now_ms)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None

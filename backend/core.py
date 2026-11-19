"""Validaciones y reglas del prototipo Paper V0.1."""
import math
import statistics
from datetime import datetime, timezone

DAY_MS = 86_400_000
ACTIONS = {"buy", "hold", "sell"}


def number(value, name, minimum=0, maximum=None, strict_min=False):
    if isinstance(value, bool):
        raise ValueError(f"{name}: se requiere un número")
    result = float(value)
    if not math.isfinite(result) or result < minimum or (strict_min and result == minimum):
        raise ValueError(f"{name}: valor fuera de rango")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name}: valor fuera de rango")
    return result


def closed_candles(rows, now_ms, max_age_h):
    if not isinstance(rows, list) or not rows:
        raise ValueError("MEXC: respuesta vacía o formato incorrecto")
    result, previous = [], None
    for row in rows:
        if not isinstance(row, list) or len(row) < 7:
            raise ValueError("MEXC: dimensiones de vela incorrectas")
        ts, end = row[0], row[6]
        if type(ts) is not int or type(end) is not int or ts < 0:
            raise ValueError("MEXC: fechas inválidas")
        if end not in {ts + DAY_MS - 1, ts + DAY_MS} or ts % DAY_MS:
            raise ValueError("MEXC: frecuencia distinta de un día UTC")
        if previous is not None and ts - previous != DAY_MS:
            raise ValueError("MEXC: fechas duplicadas, desordenadas o días faltantes")
        previous = ts
        number(row[4], "precio de cierre", strict_min=True)
        if ts > now_ms:
            raise ValueError("MEXC: fecha futura")
        if end < now_ms:
            result.append(row)
    if len(result) < 21:
        raise ValueError("MEXC: se requieren al menos 21 cierres válidos")
    if now_ms - result[-1][6] > max_age_h * 3_600_000:
        raise ValueError("MEXC: último cierre fuera de la antigüedad permitida")
    return result


def features(rows):
    closes = [float(row[4]) for row in rows[-21:]]
    returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    sma = statistics.mean(closes[-20:])
    result = {"close": closes[-1], "ret_1d": returns[-1],
              "dist_sma20": closes[-1] / sma - 1, "vol20": statistics.stdev(returns)}
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError("Indicadores no finitos")
    return result


def proposal(value, symbol, candle_ts):
    if not isinstance(value, dict):
        raise ValueError("LLM: se esperaba un objeto JSON")
    if not isinstance(value.get("action"), str) or value["action"] not in ACTIONS:
        raise ValueError("LLM: acción no permitida")
    if value.get("symbol") != symbol:
        raise ValueError("LLM: símbolo distinto al solicitado")
    if type(value.get("candle_ts")) is not int or value["candle_ts"] != candle_ts:
        raise ValueError("LLM: fecha distinta a la vela evaluada")
    reason = value.get("reason")
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 200:
        raise ValueError("LLM: justificación inválida; longitud permitida de 1 a 200")
    return {"action": value["action"], "symbol": symbol, "candle_ts": candle_ts, "reason": reason.strip()}


def paper_step(account, action, price, execution_ms, max_exposure, max_loss):
    """Registro didáctico a precio de referencia; no representa una ejecución de mercado."""
    if action not in ACTIONS:
        raise ValueError("Acción no permitida")
    number(price, "precio", strict_min=True)
    number(max_exposure, "MAX_EXPOSURE", maximum=1, strict_min=True)
    number(max_loss, "MAX_DAILY_LOSS", maximum=1, strict_min=True)
    result = dict(account)
    number(result["cash"], "efectivo")
    number(result["qty"], "posición")
    number(result["equity"], "patrimonio anterior")
    number(result["day_start"], "base diaria")
    equity = result["cash"] + result["qty"] * price
    number(equity, "patrimonio")
    today = datetime.fromtimestamp(execution_ms / 1000, timezone.utc).date().isoformat()
    if result["risk_day"] != today:
        # La primera observación del día usa como base la última valoración guardada.
        result["risk_day"] = today
        result["day_start"] = result["equity"]
        result["risk_blocked"] = False
    base = result["day_start"]
    if base <= 0 or equity <= base * (1 - max_loss):
        result["risk_blocked"] = True
    risk, final = "ok", action
    if result["risk_blocked"]:
        final, risk = "hold", "bloqueado: pérdida diaria máxima"
    elif action == "buy" and (result["qty"] > 0 or result["cash"] <= 0):
        final, risk = "hold", "rechazado: posición existente o efectivo insuficiente"
    elif action == "sell" and result["qty"] <= 0:
        final, risk = "hold", "rechazado: no hay posición que vender"
    if final == "buy":
        spend = min(result["cash"], equity * max_exposure)
        result["cash"] -= spend
        result["qty"] += spend / price
    elif final == "sell":
        result["cash"] += result["qty"] * price
        result["qty"] = 0.0
    result["equity"] = result["cash"] + result["qty"] * price
    for field in ("cash", "qty", "equity"):
        number(result[field], field)
    result["risk"] = risk
    return result, final, risk

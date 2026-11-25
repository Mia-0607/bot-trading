<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { validAmount, fresh, chart, type Candle } from './logic'
interface Quote {price: string; requested_at: number; received_at: number; expires_at: number}
interface Trade {request_id: string; side: 'buy'|'sell'; qty: string; price: string; total: string; cash: string; position: string; equity: string; recorded_at: number}
interface State {symbol: string; mode: string; cash: string; qty: string; equity: string|null; capital: string; quote: Quote|null; market_error: string|null; history: Trade[]; server_time: number}
interface Order {request_id: string; side: 'buy'|'sell'; amount: string}
const token = ref(''), msg = ref(''), error = ref(''), candleError = ref('')
const s = ref<State|null>(null), candles = ref<Candle[]>([])
const online = ref(false), connected = ref(false), busy = ref(false), refreshing = ref(false)
const buyAmount = ref('1000'), sellAmount = ref('0.001'), pending = ref<Order|null>(null)
const clock = ref(Date.now())
let timer: number | undefined, tick: number | undefined, version = 0, offset = 0
const money = (v: string|number|null) => v === null ? 'Sin valoración actual' : Number(v).toLocaleString('es-MX', {maximumFractionDigits: 2, minimumFractionDigits: 2}) + ' USDT'
const when = (t: number) => new Date(t).toLocaleString('es-MX', {timeZone: 'UTC'}) + ' UTC'
const isFresh = computed(() => fresh(s.value?.quote ?? null, clock.value))
const canTrade = computed(() => online.value && isFresh.value && !busy.value && !refreshing.value && !pending.value)
const bars = computed(() => chart(candles.value))
const pnl = computed(() => s.value?.equity === null || !s.value ? null : (Number(s.value.equity) / 50000 - 1) * 100)

async function request(path: string, body?: Order) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 12000)
  try {
    const r = await fetch(path, {method: body ? 'POST' : 'GET', signal: controller.signal,
      headers: {'X-API-Key': token.value, ...(body ? {'Content-Type': 'application/json'} : {})},
      body: body ? JSON.stringify(body) : undefined})
    if (!r.ok) {
      const data = await r.json().catch(() => ({}))
      throw new Error(r.status === 401 ? 'Credencial incorrecta.' : typeof data.detail === 'string' ? data.detail : `Solicitud rechazada (${r.status}).`)
    }
    return await r.json()
  } finally { window.clearTimeout(timeout) }
}
async function refresh() {
  if (!connected.value || refreshing.value || busy.value) return
  const v = version
  refreshing.value = true
  try {
    const data = await request('/api/state') as State
    if (data.mode !== 'paper' || data.symbol !== 'BTCUSDT' || !Array.isArray(data.history)
        || !Number.isFinite(Number(data.cash)) || !Number.isFinite(Number(data.qty))) throw new Error('Respuesta incompatible.')
    if (v !== version) return
    offset = data.server_time - Date.now()
    clock.value = Date.now() + offset
    s.value = data; online.value = true; error.value = data.market_error ?? ''
  } catch (e) {
    if (v !== version) return
    online.value = false; error.value = e instanceof Error ? e.message : 'No se pudo consultar el servidor.'
  } finally { refreshing.value = false }
}
async function refreshCandles() {
  const v = version
  try {
    const data = await request('/api/candles')
    if (v !== version) return
    candles.value = data.candles; candleError.value = ''
  } catch {
    if (v === version) candleError.value = 'No se pudieron actualizar las velas. La gráfica puede estar desactualizada.'
  }
}
async function connect() {
  if (!token.value.trim()) {error.value = 'Introduce la credencial del operador.'; return}
  version++; connected.value = true; online.value = false
  await Promise.all([refresh(), refreshCandles()])
}
function disconnect() {
  version++; connected.value = false; online.value = false; token.value = ''; s.value = null
  candles.value = []; error.value = ''; candleError.value = ''
}
async function submit(side?: 'buy'|'sell') {
  if (busy.value || refreshing.value) return
  if (side) {
    if (!canTrade.value) return
    const amount = side === 'buy' ? buyAmount.value : sellAmount.value
    if (!validAmount(amount)) { msg.value = 'Introduce una cantidad positiva con hasta 8 decimales.'; return }
    pending.value = {request_id: crypto.randomUUID(), side, amount}
  }
  if (!pending.value) return
  busy.value = true; msg.value = ''
  try {
    const result = await request('/api/trades', pending.value)
    msg.value = `Simulación registrada: ${result.side === 'buy' ? 'compra' : 'venta'} de ${result.qty} BTC a ${money(result.price)}.`
    pending.value = null
  } catch (e) {
    msg.value = (e instanceof Error ? e.message : 'Sin respuesta.') + ' Reintenta la misma solicitud para confirmar su resultado sin duplicarla.'
  } finally { busy.value = false; await refresh() }
}
function discard() {
  // Acción explícita: el usuario ya pudo revisar el historial actualizado.
  pending.value = null; msg.value = 'Solicitud descartada de la vista. Revisa el historial antes de crear otra.'
}
onMounted(() => {
  tick = window.setInterval(() => {clock.value = Date.now() + offset}, 500)
  timer = window.setInterval(() => {
    if (connected.value) {void refresh(); void refreshCandles()}
  }, 5000)
})
onUnmounted(() => {version++; window.clearInterval(timer); window.clearInterval(tick)})
</script>

<template>
  <main>
    <header><div><h1>Bot de Trading <small>V0.2</small></h1>
      <p class="muted">BTC/USDT · MEXC: datos públicos · <b>SOLO SIMULACIÓN</b></p></div>
      <span class="pill" :class="online && isFresh ? 'ok' : 'warn'">{{ online && isFresh ? 'Precio disponible' : 'Sin precio fresco confirmado' }}</span>
    </header>
    <section class="card notice">
      <b>Compras y ventas manuales con dinero ficticio</b>
      <p>Capital inicial: 50,000 USDT. Sin órdenes reales, apalancamiento ni conexión al LLM.</p>
      <p>La simulación consulta un precio nuevo al operar; puede diferir del mostrado. Comisión académica: 0%.</p>
      <p v-if="error" class="warning" role="alert">{{ error }}</p>
      <p v-if="s && (!online || !isFresh)" class="warning">Datos sin confirmar o vencidos. Operaciones bloqueadas; la última lectura no es una valoración actual.</p>
    </section>
    <section v-if="s" class="kpis">
      <div class="card"><span class="muted">Patrimonio {{ !isFresh || !online ? '(última lectura)' : '' }}</span><strong>{{ money(s.equity) }}</strong><em v-if="pnl !== null" :class="pnl >= 0 ? 'up':'down'">{{ pnl.toFixed(2) }}% vs capital inicial</em></div>
      <div class="card"><span class="muted">Efectivo ficticio</span><strong>{{ money(s.cash) }}</strong><em class="muted">Disponible para comprar</em></div>
      <div class="card"><span class="muted">Posición BTC</span><strong>{{ Number(s.qty).toFixed(8) }}</strong><em class="muted">Sin posiciones negativas</em></div>
      <div class="card"><span class="muted">Precio BTC/USDT</span><strong>{{ s.quote ? money(s.quote.price) : 'No disponible' }}</strong><em v-if="s.quote" class="muted">Consulta: {{ when(s.quote.received_at) }}</em></div>
    </section>
    <section class="grid">
      <div class="card big"><h2>Mercado · Velas de 1 minuto</h2>
        <p class="muted small">Últimas 60 velas públicas. La vela actual puede seguir formándose.</p>
        <p v-if="candleError" class="warning" role="alert">{{ candleError }}</p>
        <svg v-if="bars.length" viewBox="0 0 600 190" class="market" role="img" aria-label="Velas BTC USDT de MEXC">
          <g v-for="b in bars" :key="b.ts" :stroke="Number(b.close) >= Number(b.open) ? '#2ecc8f':'#ff5d6c'">
            <title>{{ when(b.ts) }} · Apertura {{ b.open }} · Máximo {{ b.high }} · Mínimo {{ b.low }} · Cierre {{ b.close }}</title>
            <line :x1="b.x" :x2="b.x" :y1="b.top" :y2="b.bottom" />
            <line :x1="b.x" :x2="b.x" :y1="b.openY" :y2="b.closeY === b.openY ? b.closeY + 1 : b.closeY" stroke-width="5" />
          </g>
        </svg>
        <p v-else class="muted">Conecta el backend para consultar el mercado.</p>
        <p v-if="candles.length" class="small muted">{{ when(candles[0].ts) }} — {{ when(candles[candles.length-1].ts) }}<br>Rango: {{ money(Math.min(...candles.map(c => Number(c.low)))) }} — {{ money(Math.max(...candles.map(c => Number(c.high)))) }}</p>
      </div>
      <div class="card"><h2>Control del operador</h2>
        <label for="key">Credencial del operador</label>
        <input id="key" v-model="token" type="password" autocomplete="off" :disabled="connected || busy" />
        <p class="small muted">Solo en memoria. No necesitas una clave de MEXC ni del profesor.</p>
        <div class="btns"><button v-if="!connected" :disabled="busy || refreshing" @click="connect">Conectar</button><button v-else :disabled="busy || refreshing || !!pending" @click="disconnect">Desconectar</button><button :disabled="!connected || refreshing || busy" @click="refresh">Actualizar</button></div>
        <label for="buy">Importe de compra (USDT)</label><input id="buy" v-model="buyAmount" inputmode="decimal" :disabled="busy || !!pending" />
        <div class="btns"><button class="go" :disabled="!canTrade || !validAmount(buyAmount)" @click="submit('buy')">Comprar BTC · simulado</button></div>
        <label for="sell">Cantidad a vender (BTC)</label><input id="sell" v-model="sellAmount" inputmode="decimal" :disabled="busy || !!pending" />
        <div class="btns"><button class="stop" :disabled="!canTrade || !validAmount(sellAmount)" @click="submit('sell')">Vender BTC · simulado</button></div>
        <p v-if="msg" role="status" aria-live="polite" class="small">{{ msg }}</p>
        <div v-if="pending && !busy" class="notice"><p class="small">Solicitud pendiente: {{ pending.side === 'buy' ? 'compra USDT' : 'venta BTC' }} {{ pending.amount }}. Revisa el historial o confirma con el mismo identificador.</p><div class="btns"><button :disabled="refreshing" @click="submit()">Reintentar sin duplicar</button><button :disabled="refreshing || !online" @click="discard">Descartar solicitud</button></div></div>
      </div>
    </section>
    <section v-if="s" class="card"><h2>Historial de operaciones simuladas</h2><p class="small muted">Últimas 100 operaciones. El historial completo permanece en SQLite.</p>
      <table><thead><tr><th>Fecha UTC</th><th>Acción</th><th>BTC</th><th>Precio</th><th>Total</th><th>Efectivo posterior</th><th>Patrimonio al operar</th></tr></thead>
        <tbody><tr v-for="h in s.history" :key="h.request_id"><td>{{ when(h.recorded_at) }}</td><td><span class="tag" :class="h.side">{{ h.side === 'buy' ? 'COMPRA':'VENTA' }}</span></td><td>{{ h.qty }}</td><td>{{ money(h.price) }}</td><td>{{ money(h.total) }}</td><td>{{ money(h.cash) }}</td><td>{{ money(h.equity) }}</td></tr><tr v-if="!s.history.length"><td colspan="7">Sin operaciones registradas.</td></tr></tbody>
      </table>
    </section>
    <footer class="muted small">V0.2 · Vue + TypeScript + Vite · FastAPI + SQLite · Dinero ficticio, datos públicos reales.</footer>
  </main>
</template>
<style>
:root { --bg:#0e1117; --card:#171b24; --line:#262c3a; --tx:#e6e9ef; --mu:#8b93a7; --up:#2ecc8f; --dn:#ff5d6c; --am:#f5b94a; --ac:#6c8cff }
* { box-sizing: border-box } body { margin:0; background:var(--bg); color:var(--tx); font:15px/1.5 system-ui,sans-serif }
main { max-width:1080px; margin:0 auto; padding:24px 16px 40px; display:grid; gap:16px }
header { display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px }
h1 { margin:0; font-size:26px } h1 small { color:var(--ac); font-size:14px } h2 { margin:0 0 10px; font-size:14px; text-transform:uppercase; letter-spacing:.06em; color:var(--mu) }
.muted { color:var(--mu) } .small { font-size:12.5px } .up { color:var(--up) } .down { color:var(--dn) }
.pills { display:flex; gap:8px } .pill { padding:4px 12px; border-radius:99px; border:1px solid var(--line); font-size:13px }
.pill.ok,.pill.running { color:var(--up); border-color:var(--up) } .pill.warn,.pill.paused { color:var(--am); border-color:var(--am) } .pill.stopped { color:var(--dn); border-color:var(--dn) }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; overflow-x:auto }
.kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px }
.kpis .card { display:grid; gap:2px } .kpis strong { font-size:22px } .kpis em { font-style:normal; font-size:12.5px }
.grid { display:grid; grid-template-columns:2fr 1fr; gap:12px } @media (max-width:760px){ .grid{grid-template-columns:1fr} }
.action { font-size:34px; font-weight:800; letter-spacing:.04em } .action.buy{color:var(--up)} .action.sell{color:var(--dn)} .action.hold{color:var(--am)}
.reason { margin:4px 0 14px } dl { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin:0 }
dt { color:var(--mu); font-size:12px } dd { margin:0; font-weight:600 }
input { width:100%; padding:9px 10px; border-radius:8px; border:1px solid var(--line); background:#0e1117; color:var(--tx) }
.btns { display:flex; gap:8px; margin:10px 0 } button { flex:1; padding:9px; border-radius:8px; border:1px solid var(--line); background:#202636; color:var(--tx); cursor:pointer; font-weight:600 }
button.go { background:var(--up); color:#06210f; border:0 } button.stop { background:var(--dn); color:#2a0509; border:0 }
.spark { width:100%; height:64px; color:var(--ac) }
table { width:100%; border-collapse:collapse; font-size:14px } th,td { text-align:left; padding:8px 6px; border-bottom:1px solid var(--line); white-space:nowrap }
th { color:var(--mu); font-weight:500; font-size:12px } td:nth-child(4){ white-space:normal }
.tag { padding:2px 8px; border-radius:6px; font-size:12px; font-weight:700 } .tag.buy{background:#12392c;color:var(--up)} .tag.sell{background:#44171d;color:var(--dn)} .tag.hold{background:#3d3217;color:var(--am)}
.errs { margin:12px 0 0; padding:0; list-style:none; color:var(--am); font-size:13px } footer { text-align:center }
.notice { border-left:3px solid var(--ac) } .notice p { margin:6px 0 } .warning { color:var(--am) }
button:disabled { opacity:.5; cursor:not-allowed } button:focus-visible,input:focus-visible { outline:2px solid var(--ac); outline-offset:3px }
label { display:block; margin-bottom:6px } .btns { flex-wrap:wrap } .btns button { min-width:75px }
</style>

<style>.market {width:100%; min-height:180px}</style>

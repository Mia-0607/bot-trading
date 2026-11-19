<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

type Action = 'buy' | 'hold' | 'sell'
interface Decision { ts: number; action: Action; proposed_action: Action; reason: string; risk: string; forecast: number; equity: number }
interface State {
  symbol: string; status: 'running' | 'paused' | 'stopped'; risk: string; mode: string
  cash: number; qty: number; equity: number; capital: number
  max_data_age_hours: number
  last: { ts: number; data_close_ts: number; close: number; ret_1d: number; dist_sma20: number; vol20: number; forecast: number; proposed_action: Action; action: Action; reason: string; risk: string } | null
  history: Decision[]; errors: { ts: number; msg: string }[]
}

// Datos ficticios exclusivos del modo demostración; no se usan como respaldo del servidor.
const DEMO: State = {
  symbol: 'BTCUSDT', status: 'stopped', risk: 'ok', mode: 'demo', cash: 50000, qty: 0, equity: 50000, capital: 50000, max_data_age_hours: 48,
  last: { ts: Date.UTC(2026, 10, 16), data_close_ts: Date.UTC(2026, 10, 17) - 1, close: 97250.4, ret_1d: 0.0123, dist_sma20: 0.034, vol20: 0.021, forecast: 0, proposed_action: 'hold', action: 'hold', risk: 'ok', reason: 'Ejemplo de presentación. Pronóstico de referencia igual a cero.' },
  history: [
    { ts: Date.UTC(2026, 10, 16), action: 'hold', proposed_action: 'hold', risk: 'ok', reason: 'Ejemplo: sin cambio de posición.', forecast: 0, equity: 50000 },
    { ts: Date.UTC(2026, 10, 15), action: 'hold', proposed_action: 'sell', risk: 'rechazado: no hay posición que vender', reason: 'Ejemplo de propuesta rechazada por riesgo.', forecast: 0, equity: 50000 },
  ], errors: [],
}
const copyDemo = (): State => structuredClone(DEMO)
const s = ref<State>(copyDemo())
const demo = ref(true)
const online = ref(false)
// La credencial del operador se mantiene solo durante la sesión de la página.
const token = ref('')
try { sessionStorage.removeItem('op_key') } catch { /* La interfaz no depende del almacenamiento del navegador. */ }
const msg = ref('')
const connectionError = ref('')
const busy = ref(false)
const refreshing = ref(false)
const lastSync = ref<number | null>(null)
const clock = ref(Date.now())
let timer: number | undefined
let viewVersion = 0

function isState(value: unknown): value is State {
  if (!value || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  const finite = (n: unknown) => typeof n === 'number' && Number.isFinite(n)
  const action = (a: unknown) => a === 'buy' || a === 'hold' || a === 'sell'
  const decision = (d: unknown) => {
    if (!d || typeof d !== 'object') return false
    const r = d as Record<string, unknown>
    return finite(r.ts) && finite(r.forecast) && finite(r.equity) && action(r.action)
      && action(r.proposed_action) && typeof r.reason === 'string' && typeof r.risk === 'string'
  }
  if (typeof v.symbol !== 'string' || typeof v.risk !== 'string' || v.mode !== 'paper_prototype'
      || !['running', 'paused', 'stopped'].includes(String(v.status))
      || !['cash', 'qty', 'equity', 'capital', 'max_data_age_hours'].every(k => finite(v[k]))
      || Number(v.capital) <= 0 || Number(v.max_data_age_hours) <= 0
      || !Array.isArray(v.history) || !v.history.every(decision)
      || !Array.isArray(v.errors) || !v.errors.every(e => e && finite(e.ts) && typeof e.msg === 'string')) return false
  if (v.last !== null) {
    if (!decision(v.last)) return false
    const last = v.last as Record<string, unknown>
    if (!['close', 'ret_1d', 'dist_sma20', 'vol20', 'data_close_ts'].every(k => finite(last[k]))) return false
  }
  return true
}

async function request(path: string, method = 'GET') {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 10000)
  try {
    const response = await fetch(path, { method, headers: { 'X-API-Key': token.value }, signal: controller.signal })
    if (!response.ok) throw new Error(response.status === 401 ? 'Credencial del operador ausente o incorrecta.' : `El servidor respondió con error ${response.status}.`)
    return await response.json()
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw new Error('Tiempo de espera agotado. Estado sin confirmar.')
    throw error
  } finally { window.clearTimeout(timeout) }
}

async function refresh() {
  if (demo.value || refreshing.value) return
  const version = viewVersion
  refreshing.value = true
  try {
    const data: unknown = await request('/api/state')
    if (!isState(data)) throw new Error('La respuesta del servidor no coincide con el formato esperado.')
    if (version !== viewVersion) return
    s.value = data; online.value = true; lastSync.value = Date.now(); connectionError.value = ''
  } catch (error) {
    if (version !== viewVersion) return
    online.value = false
    connectionError.value = error instanceof Error ? error.message : 'No fue posible consultar el backend.'
  } finally { refreshing.value = false }
}

async function connect() {
  if (!token.value.trim()) { msg.value = 'Falta la credencial del operador.'; return }
  viewVersion++
  demo.value = false; online.value = false; lastSync.value = null; msg.value = ''
  s.value = { ...copyDemo(), mode: 'paper_prototype', last: null, history: [], errors: [] }
  await refresh()
}

function useDemo() {
  viewVersion++
  demo.value = true; online.value = false; token.value = ''; lastSync.value = null
  connectionError.value = ''; msg.value = ''; s.value = copyDemo()
}
async function cmd(c: 'start' | 'pause' | 'stop') {
  if (busy.value) return
  if (demo.value) {
    s.value.status = c === 'start' ? 'running' : c === 'pause' ? 'paused' : 'stopped'
    msg.value = 'Cambio visual de demostración. No se envió ninguna orden al backend.'
    return
  }
  busy.value = true; msg.value = ''
  try {
    await request(`/api/${c}`, 'POST')
    msg.value = `Comando «${c}» confirmado por el servidor.`
    await refresh()
  } catch (error) {
    online.value = false
    msg.value = (error instanceof Error ? error.message : 'Error de conexión.') + ' No se puede confirmar el estado del bot.'
  } finally { busy.value = false }
}
onMounted(() => { timer = window.setInterval(() => { clock.value = Date.now(); void refresh() }, 5000) })
onUnmounted(() => { viewVersion++; window.clearInterval(timer) })

const pnl = computed(() => s.value.capital > 0 ? s.value.equity / s.value.capital - 1 : 0)
const visibleData = computed(() => demo.value || lastSync.value !== null)
const stale = computed(() => !demo.value && !!s.value.last && clock.value - s.value.last.data_close_ts > s.value.max_data_age_hours * 3600000)
const pct = (x: number, d = 2) => `${(x * 100).toFixed(d)}%`
const money = (x: number) => `${x.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT`
const when = (t: number) => `${new Date(t).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short', timeZone: 'UTC' })} UTC`
const spark = computed(() => {
  const v = [...s.value.history].reverse().map(h => h.equity).concat(s.value.equity)
  if (v.length < 2) return ''
  const lo = Math.min(...v), hi = Math.max(...v), r = hi - lo || 1
  return v.map((y, i) => `${(i / (v.length - 1)) * 300},${58 - ((y - lo) / r) * 52}`).join(' ')
})
const label: Record<Action, string> = { buy: 'COMPRAR', hold: 'MANTENER', sell: 'VENDER' }
</script>

<template>
  <main>
    <header>
      <div><h1>Bot de Trading <small>V0.1</small></h1>
        <p class="muted">{{ s.symbol }} · {{ demo ? 'Datos ficticios' : 'MEXC: datos públicos' }} · <b>Prototipo Paper</b> · sin órdenes reales</p></div>
      <div class="pills">
        <span class="pill" :class="online ? 'ok' : 'warn'">{{ demo ? 'Demostración' : online ? 'Backend conectado' : 'Sin conexión confirmada' }}</span>
        <span class="pill" :class="s.status">{{ !demo && !online ? 'Estado sin confirmar' : s.status === 'running' ? 'En ejecución' : s.status === 'paused' ? 'Pausado' : 'Detenido' }}</span>
      </div>
    </header>

    <section class="card notice" aria-label="Alcance de la versión">
      <b>V0.1 · Interfaz y conexión preliminar</b>
      <p>Pronóstico de referencia: cero. Modelo entrenado y API privada del profesor pendientes de integración.</p>
      <p v-if="demo">Datos ficticios para revisar el diseño. Los botones solo cambian el estado visual.</p>
      <p v-else>Simulación didáctica al último cierre conocido. No representa ejecución de mercado ni resultados de una estrategia validada.</p>
      <p v-if="lastSync" class="small">Última consulta confirmada: {{ when(lastSync) }}. {{ !online ? 'Se conserva la última lectura; puede estar desactualizada.' : '' }}</p>
      <p v-if="stale" class="warning">La última vela supera la antigüedad permitida.</p>
      <p v-if="connectionError" class="warning" role="alert">{{ connectionError }}</p>
    </section>

    <section v-if="visibleData" class="kpis">
      <div class="card"><span class="muted">Patrimonio</span><strong>{{ money(s.equity) }}</strong>
        <em :class="pnl >= 0 ? 'up' : 'down'">{{ pct(pnl) }} vs capital inicial</em></div>
      <div class="card"><span class="muted">Efectivo</span><strong>{{ money(s.cash) }}</strong><em class="muted">Capital inicial {{ money(s.capital) }}</em></div>
      <div class="card"><span class="muted">Posición</span><strong>{{ s.qty > 0 ? s.qty.toFixed(6) : 'Sin posición' }}</strong><em class="muted">Sin apalancamiento ni cortos</em></div>
      <div class="card"><span class="muted">Estado de riesgo</span><strong :class="s.risk === 'ok' ? 'up' : 'down'">{{ s.risk === 'ok' ? 'Normal' : s.risk }}</strong><em class="muted">Límites fijados en el servidor</em></div>
    </section>

    <section class="grid">
      <div v-if="visibleData" class="card big">
        <h2>Decisión actual</h2>
        <template v-if="s.last">
          <p class="small muted">Propuesta del LLM {{ demo ? '(ejemplo)' : '' }}: {{ label[s.last.proposed_action] }}</p>
          <div class="action" :class="s.last.action">{{ label[s.last.action] }}</div>
          <p class="small">Resultado después de riesgo: {{ s.last.risk === 'ok' ? 'Permitido' : s.last.risk }}. {{ s.last.action === 'hold' ? (s.qty > 0 ? 'Se conserva la posición.' : 'Se permanece en efectivo.') : '' }}</p>
          <p class="reason">{{ s.last.reason }}</p>
          <dl>
            <div><dt>Cierre de la vela</dt><dd>{{ when(s.last.data_close_ts) }}</dd></div>
            <div><dt>Cierre</dt><dd>{{ money(s.last.close) }}</dd></div>
            <div><dt>Referencia cero (t+1)</dt><dd>{{ pct(s.last.forecast, 3) }}</dd></div>
            <div><dt>Dist. SMA20</dt><dd>{{ pct(s.last.dist_sma20) }}</dd></div>
            <div><dt>Volatilidad 20d</dt><dd>{{ pct(s.last.vol20) }}</dd></div>
            <div><dt>Rend. 1d</dt><dd>{{ pct(s.last.ret_1d) }}</dd></div>
          </dl>
        </template>
        <p v-else class="muted">Sin decisiones registradas.</p>
      </div>

      <div class="card">
        <h2>Control del operador</h2>
        <label for="operator-key">Credencial del operador</label>
        <input id="operator-key" v-model="token" :disabled="busy || refreshing" type="password" placeholder="Acceso al backend local" autocomplete="off" />
        <p class="muted small">Credencial independiente de la API del LLM. Se mantiene solo en memoria hasta cerrar o recargar la página.</p>
        <div class="btns">
          <button :disabled="busy || refreshing" @click="connect">Conectar</button>
          <button :disabled="busy || refreshing || demo" @click="useDemo">Ver demo</button>
        </div>
        <p v-if="!demo" class="small muted">Cambiar de vista no pausa ni detiene el backend.</p>
        <div class="btns">
          <button class="go" :disabled="busy || (!demo && !online)" @click="cmd('start')">Iniciar</button>
          <button :disabled="busy || (!demo && !token)" @click="cmd('pause')">Pausar</button>
          <button class="stop" :disabled="busy || (!demo && !token)" @click="cmd('stop')">Detener</button>
        </div>
        <p class="muted small">Detener bloquea nuevas órdenes y <b>no liquida</b> la posición.</p>
        <p v-if="msg" class="small" role="status" aria-live="polite">{{ msg }}</p>
        <h2>Patrimonio</h2>
        <svg v-if="visibleData" viewBox="0 0 300 64" class="spark" role="img" aria-label="Patrimonio de las últimas decisiones"><polyline :points="spark" fill="none" stroke="currentColor" stroke-width="2" /></svg>
      </div>
    </section>

    <section v-if="visibleData" class="card">
      <h2>Historial de decisiones</h2>
      <table>
        <thead><tr><th>Inicio de vela</th><th>Propuesta / resultado</th><th>Referencia cero</th><th>Motivo / riesgo</th><th>Patrimonio</th></tr></thead>
        <tbody>
          <tr v-for="h in s.history" :key="h.ts">
            <td>{{ when(h.ts) }}</td><td>{{ label[h.proposed_action] }} / <span class="tag" :class="h.action">{{ label[h.action] }}</span></td>
            <td>{{ pct(h.forecast, 3) }}</td><td>{{ h.reason }}<br /><span class="muted">{{ h.risk }}</span></td><td>{{ money(h.equity) }}</td>
          </tr>
          <tr v-if="!s.history.length"><td colspan="5" class="muted">Sin registros.</td></tr>
        </tbody>
      </table>
      <ul v-if="s.errors.length" class="errs"><li v-for="(e, index) in s.errors" :key="`${e.ts}-${index}`">⚠ {{ when(e.ts) }} · {{ e.msg }}</li></ul>
    </section>
    <footer class="muted small">V0.1 · Vue 3 + TypeScript + Vite · FastAPI · SQLite · Adaptador para Ollama local. Sin claves del LLM en la interfaz.</footer>
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

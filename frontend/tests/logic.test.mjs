import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {validAmount, fresh, chart} from '../src/logic.ts'

test('cantidades positivas, finitas y con precisión limitada', () => {
  for (const v of ['0','-1','NaN','Infinity','1e3','1.000000001','', '1000000001']) assert.equal(validAmount(v), false, v)
  for (const v of ['1000','0.00000001','1.25']) assert.equal(validAmount(v), true, v)
})
test('bloqueo cuando la cotización vence o no existe', () => {
  assert.equal(fresh(null, 1), false)
  assert.equal(fresh({expires_at: 10}, 9), true)
  assert.equal(fresh({expires_at: 10}, 10), false)
  assert.equal(fresh({expires_at: NaN}, 9), false)
})
test('gráfica plana y gráfica de precios sin coordenadas inválidas', () => {
  const rows = [{ts:1,end:2,open:'10',high:'10',low:'10',close:'10'}]
  assert.ok(chart(rows).every(b => [b.x,b.top,b.bottom,b.openY,b.closeY].every(Number.isFinite)))
  assert.deepEqual(chart([]), [])
})
test('interfaz conserva protección, simulación explícita y reintento identificable', () => {
  const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
  assert.match(app, /SOLO SIMULACIÓN/)
  assert.match(app, /crypto.randomUUID/)
  assert.match(app, /X-API-Key/)
  assert.doesNotMatch(app, /localStorage|sessionStorage|LLM_API_KEY|api\/start/)
})

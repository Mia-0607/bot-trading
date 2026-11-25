// Pruebas aisladas de estado y red. No sustituyen la compilación ni las pruebas visuales de Vue.
import { readFileSync } from 'node:fs'
import { stripTypeScriptTypes } from 'node:module'
import vm from 'node:vm'
import test from 'node:test'
import assert from 'node:assert/strict'

const source = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1]
  .replace(/^import .* from 'vue'\r?\n/m, '')

function setup() {
  let calls = 0
  let response = async () => { throw new Error('Conexión no disponible') }
  const context = vm.createContext({
    ref: value => ({ value }), computed: get => ({ get value() { return get() } }),
    onMounted: () => {}, onUnmounted: () => {}, structuredClone, AbortController,
    sessionStorage: { removeItem: () => {} },
    window: { setTimeout, clearTimeout, setInterval, clearInterval },
    fetch: async (...args) => { calls++; return response(...args) },
  })
  vm.runInContext(stripTypeScriptTypes(script) + '\n globalThis.ui = {s,demo,online,token,msg,lastSync,connectionError,cmd,connect,useDemo,refresh,isState,copyDemo};', context)
  return { ui: context.ui, calls: () => calls, respond: fn => { response = fn } }
}

function validState(ui) {
  const data = ui.copyDemo()
  data.mode = 'paper_prototype'
  data.last.equity = data.equity
  return data
}

test('Los controles demo no hacen solicitudes de red', async () => {
  const {ui, calls} = setup()
  await ui.cmd('start')
  assert.equal(ui.s.value.status, 'running')
  assert.equal(calls(), 0)
})

test('Una conexión fallida no convierte el modo servidor en demo', async () => {
  const {ui} = setup()
  ui.token.value = 'test-only'
  await ui.connect()
  assert.equal(ui.demo.value, false)
  assert.equal(ui.online.value, false)
  assert.equal(ui.lastSync.value, null)
  assert.equal(ui.s.value.last, null)
})

test('La desconexión conserva la última lectura confirmada', async () => {
  const {ui, respond} = setup()
  const data = validState(ui)
  data.equity = 50123
  respond(async () => ({ok: true, json: async () => data}))
  ui.token.value = 'test-only'
  await ui.connect()
  assert.equal(ui.online.value, true)
  respond(async () => { throw new Error('Desconexión') })
  await ui.refresh()
  assert.equal(ui.online.value, false)
  assert.equal(ui.s.value.equity, 50123)
  assert.notEqual(ui.lastSync.value, null)
})

test('Una credencial incorrecta se informa sin inventar estado', async () => {
  const {ui, respond} = setup()
  respond(async () => ({ok: false, status: 401}))
  ui.token.value = 'test-only'
  await ui.connect()
  assert.match(ui.connectionError.value, /Credencial/)
  assert.equal(ui.lastSync.value, null)
})

test('Se rechazan respuestas con cifras no finitas o acciones inválidas', () => {
  const {ui} = setup()
  const data = validState(ui)
  assert.equal(ui.isState(data), true)
  data.equity = NaN
  assert.equal(ui.isState(data), false)
  data.equity = 50000
  data.history[0].action = 'withdraw'
  assert.equal(ui.isState(data), false)
})

test('El fallo de un comando no se comunica como ejecución confirmada', async () => {
  const {ui} = setup()
  ui.demo.value = false
  ui.token.value = 'test-only'
  await ui.cmd('stop')
  assert.equal(ui.online.value, false)
  assert.match(ui.msg.value, /No se puede confirmar/)
})

test('Volver a la demostración borra la credencial de la página', () => {
  const {ui} = setup()
  ui.token.value = 'test-only'
  ui.useDemo()
  assert.equal(ui.token.value, '')
  assert.equal(ui.demo.value, true)
})

export function validAmount(value: string): boolean {
  return /^\d+(\.\d{1,8})?$/.test(value) && Number(value) > 0 && Number(value) <= 1e9
}
export function fresh(quote: {expires_at: number} | null, now: number): boolean {
  return !!quote && Number.isFinite(quote.expires_at) && now < quote.expires_at
}
export interface Candle { ts: number; end: number; open: string; high: string; low: string; close: string }
export function chart(rows: Candle[]) {
  const lo = Math.min(...rows.map(r => Number(r.low)))
  const hi = Math.max(...rows.map(r => Number(r.high)))
  const y = (v: string) => 170 - (Number(v) - lo) / (hi - lo || 1) * 150
  return rows.map((r, i) => ({ ...r, x: 15 + i * 570 / Math.max(1, rows.length - 1),
    top: y(r.high), bottom: y(r.low), openY: y(r.open), closeY: y(r.close) }))
}

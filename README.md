# Bot de Trading · V0.2

Dashboard Vue 3 + TypeScript + Vite, con FastAPI y SQLite. Consulta datos públicos BTC/USDT de MEXC y permite comprar y vender **solo con dinero ficticio**. Capital inicial: **50,000 USDT**, una sola cuenta local persistente.

## Funciones

- Precio público y últimas 60 velas de un minuto; actualización del dashboard cada 5 segundos.
- Compra por importe USDT y venta por cantidad BTC. Saldo, posición y patrimonio actualizados.
- Historial persistente: fecha UTC, precio consultado, cantidad, importe, saldos y valoración al operar.
- Todas las rutas `/api/*` requieren `X-API-Key`, usando `OPERATOR_API_KEY` del backend.
- La credencial del operador permanece en memoria del navegador. No se envía a MEXC.
- Sin órdenes reales, claves privadas MEXC, LLM ni servicio Ollama.

## Qué se conserva de V0.1

Se conservan Vue, TypeScript, Vite, FastAPI, SQLite, la paleta oscura, tarjetas de saldos, panel del operador e historial. Los controles del ciclo automático se sustituyen por compras y ventas manuales. El código anterior de la interfaz y del servidor queda en `frontend/legacy_v01` y `backend/legacy_v01`, como referencia sin ejecución automática. `backend/core.py` y sus pruebas anteriores se conservan.

Los documentos anteriores en `docs` describen V0.1. Este README y `docs/VERIFICACION_V02.md` describen V0.2. Los límites experimentales de exposición y pérdida diaria del ciclo antiguo **no se aplican a las operaciones manuales V0.2**: estas controlan saldo disponible, posición, precisión y precio reciente.

La base nueva `backend/bot-v02.db` inicia una sola vez en 50,000 USDT y no reinicia el saldo al recargar. No migra ni sobrescribe `bot-v01.db`. No se incluyen bases personales, credenciales, entornos instalados ni historial `.git` en el paquete.

## Instalar en Windows

Coloca esta carpeta como `bot-trading\bot-trading-v0.2`, junto a V0.1. No necesitas sustituir ni borrar V0.1. Requisitos: Python 3.10+ y Node.js **22.18+** (para ejecutar las pruebas TypeScript directamente con Node).

Abre PowerShell en `bot-trading-v0.2`:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
```

Genera una clave propia sin mostrarla en la terminal (solo la primera vez; no sobrescribas un `.env` ya configurado):

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; import secrets; p=Path('.env'); assert 'OPERATOR_API_KEY=\n' in p.read_text(); p.write_text(p.read_text().replace('OPERATOR_API_KEY=\n', 'OPERATOR_API_KEY='+secrets.token_urlsafe(32)+'\n'))"
```

Abre `backend/.env` localmente y copia su clave al campo de operador de la interfaz. No la compartas ni la guardes en el código. El servidor no inicia con una clave vacía o menor de 24 caracteres.

Desde `backend`, inicia el servidor:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

En otra terminal, desde `bot-trading-v0.2`:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Abre http://127.0.0.1:5173, introduce tu credencial y pulsa **Conectar**. Mantén ambas terminales abiertas. `Ctrl+C` detiene cada servicio. No hace falta activar el entorno Python ni modificar la política de PowerShell.

## Comprobar el funcionamiento

1. Conectar y comprobar cotización, fecha de consulta, velas y 50,000 USDT iniciales.
2. Comprar 1,000 USDT ficticios. Debe reducirse efectivo y aparecer BTC e historial.
3. Vender una cantidad menor o igual a la posición. El saldo USDT aumenta.
4. Intentar comprar más saldo del disponible o vender más BTC: debe rechazarse sin modificar saldos.
5. Reiniciar el backend: saldos e historial se conservan.
6. Si falla MEXC, se bloquean operaciones y se muestra el error; nunca se sustituyen precios por datos inventados.

El precio cambia entre consulta y operación. El backend obtiene una cotización nueva para cada operación. Si una respuesta se pierde, **Reintentar sin duplicar** reutiliza el mismo identificador. Antes de descartar una solicitud o recargar la página, revisa el historial: una operación podría haberse guardado aunque el navegador no recibiera la confirmación. Los identificadores pendientes no se guardan al recargar.

## Pruebas

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Desde `frontend`:

```powershell
npm test
npm run build
```

Las pruebas backend usan respuestas MEXC controladas y bases temporales; no alteran tu saldo. Las pruebas frontend cubren lógica de importes, vigencia y gráfica; no sustituyen una prueba de la interfaz en navegador. Resultados y limitaciones en `docs/VERIFICACION_V02.md`.

## API

| Ruta | Función |
|---|---|
| `GET /api/state` | Saldo, posición, cotización, valoración y últimas 100 operaciones |
| `GET /api/candles` | Últimas 60 velas públicas de 1 minuto |
| `GET /api/history?limit=100&offset=0` | Historial paginado, hasta 500 filas por consulta |
| `POST /api/trades` | Compra o venta simulada; campos `request_id` UUID, `side` buy/sell, `amount` texto decimal |

En compra, `amount` indica USDT; en venta, BTC. No se acepta precio del cliente ni campos adicionales. Error 401: clave; 422: formato; 409: saldo, precisión, precio vencido o identificador reutilizado con contenido diferente; 503: mercado o persistencia no disponibles. `/docs` ofrece el esquema público de la API, sin saldos ni secretos.

## Modelo de simulación y límites

- Cálculos contables con Decimal; BTC hasta 8 decimales. Compra redondeada hacia abajo; solo se descuenta el importe realmente simulado y el sobrante queda en efectivo.
- Sin comisión ni deslizamiento, sin mínimos de negociación reales del exchange y sin órdenes limitadas. No reproduce ejecución real ni garantiza rentabilidad.
- Precio de referencia: ticker público consultado después de recibir la solicitud. Se exige un máximo de 10 segundos desde el inicio de esa consulta hasta la transacción SQLite. Timeout HTTP: 6 segundos.
- El ticker público no incluye fecha de la última negociación: las fechas guardadas indican **consulta y recepción**, no una certificación de antigüedad de la operación bursátil. Las velas se validan por fechas y OHLC; la última puede estar abierta.
- Saldo e historial se guardan en una misma transacción SQLite. Un UUID repetido con el mismo importe devuelve el registro original; con otro importe se rechaza. Usar un solo proceso de backend.
- Si no existe precio válido, el servidor devuelve patrimonio `null`, conserva efectivo e historial y bloquea operaciones nuevas. La interfaz identifica la última lectura cuando pierde conexión.
- Ejecución local en 127.0.0.1. GitHub almacena el código; GitHub Pages no ejecuta FastAPI/SQLite. Un despliegue en red requiere configuración adicional.

## Publicar un commit en el mismo GitHub

El paquete no trae `.git`. Para mantener el historial y V0.1 intacta, crea una copia de trabajo desde tu repositorio existente en una tercera carpeta. Desde `bot-trading`:

```powershell
git clone --no-hardlinks .\bot-trading-v0.1 .\bot-trading-publicacion-v0.2
$repoUrl = git -C .\bot-trading-v0.1 remote get-url origin
git -C .\bot-trading-publicacion-v0.2 remote set-url origin $repoUrl
git -C .\bot-trading-publicacion-v0.2 switch -c version-v0.2
robocopy .\bot-trading-v0.2 .\bot-trading-publicacion-v0.2 /E /XD node_modules .venv __pycache__ dist .git /XF .env *.db *.db-shm *.db-wal *.pyc
cd bot-trading-publicacion-v0.2
git status --short
git add README.md .env.example .gitignore backend frontend docs
git diff --cached --stat
git diff --cached
```

Revisa que no haya claves ni bases. Vuelve a ejecutar pruebas y compilación allí antes de publicar. Si `git clone` o cualquier paso falla, detente y revisa el mensaje. En robocopy, códigos 0 a 7 normalmente indican éxito o diferencias; 8 o más indican error.

```powershell
git commit -m "V0.2: mercado MEXC y trading manual simulado"
git push -u origin version-v0.2
```

En GitHub abre una solicitud de cambios de `version-v0.2` hacia tu rama principal. Así revisas la entrega antes de incorporarla. Opcionalmente, tras revisar el commit:

```powershell
git tag v0.2.0
git push origin v0.2.0
```

Estos comandos se proporcionan para que publiques la versión; no se ejecutó ningún commit ni push durante la preparación.

## Referencia

[Documentación oficial de MEXC Spot](https://mexcdevelop.github.io/apidocs/spot_v3_en/): endpoints públicos `GET /api/v3/ticker/price` y `GET /api/v3/klines`.

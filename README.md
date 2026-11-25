# Bot de Trading · V0.2

Aplicación de simulación de compraventa de Bitcoin con datos públicos de MEXC. Integra un dashboard desarrollado con Vue, TypeScript y Vite, un backend FastAPI y almacenamiento persistente en SQLite.

Las operaciones utilizan exclusivamente dinero ficticio. El capital inicial es de **50,000 USDT**. No se ejecutan órdenes reales ni se requieren credenciales privadas de MEXC o un servicio LLM.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Interfaz | Vue 3, TypeScript y Vite |
| API local | Python y FastAPI |
| Consulta de mercado | httpx y API pública de MEXC |
| Persistencia | SQLite |
| Pruebas | unittest y Node.js |

## Funcionalidades

- Consulta del precio de BTC/USDT y de las últimas 60 velas de un minuto.
- Actualización del dashboard cada cinco segundos.
- Compra simulada por importe en USDT y venta simulada por cantidad de BTC.
- Cálculo de efectivo disponible, posición en BTC y patrimonio.
- Registro de fecha, precio, cantidad, importe y saldos de cada operación.
- Recuperación de saldos e historial después de reiniciar el servidor.
- Validación de importes, saldo disponible, posición y vigencia de la consulta de precio.
- Identificadores de solicitud para evitar operaciones duplicadas al reintentar.
- Autenticación mediante una credencial del operador.

## Estructura

```text
bot-trading-v0.2/
├── backend/
│   ├── main.py
│   ├── paper.py
│   ├── core.py
│   ├── requirements.txt
│   ├── tests/
│   └── legacy_v01/
├── frontend/
│   ├── src/
│   ├── tests/
│   ├── legacy_v01/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

Las carpetas `legacy_v01` contienen código de referencia de la versión anterior. El servidor V0.2 no ejecuta el ciclo automático del LLM. Los documentos identificados como V0.1 corresponden a esa versión.

## Requisitos

- Python 3.10 o posterior.
- Node.js 22.18 o posterior y npm.
- Acceso a Internet para consultar MEXC.

## Instalación en Windows

La configuración siguiente utiliza un entorno virtual Python en la carpeta superior al proyecto. Ese entorno puede compartirse entre versiones con dependencias compatibles:

```text
bot-trading/
├── .venv/
├── bot-trading-v0.1/
└── bot-trading-v0.2/
```

### Backend

Desde la raíz de `bot-trading-v0.2`, creación inicial del entorno e instalación de dependencias:

```powershell
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

La creación del entorno se omite cuando ya existe. Las dependencias se instalan inicialmente y cuando cambian los requisitos.

Creación del archivo de configuración, únicamente si todavía no existe:

```powershell
if (-not (Test-Path .\backend\.env)) {
    Copy-Item .\.env.example .\backend\.env
}
```

`backend/.env` debe definir `OPERATOR_API_KEY` con una credencial de al menos 24 caracteres. Generación de un valor aleatorio:

```powershell
..\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

El valor generado se asigna a `OPERATOR_API_KEY` en el archivo local. La misma credencial permite conectar el dashboard con el backend. Los cambios en `.env` requieren reiniciar el servidor.

### Frontend

Desde la raíz del proyecto:

```powershell
cd frontend
npm ci
```

Las dependencias del frontend se administran por proyecto mediante `package-lock.json`. No forman parte del entorno virtual Python.

## Ejecución

### Servidor backend

Desde la raíz del proyecto:

```powershell
cd backend
..\..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

### Interfaz

En una segunda terminal, desde la raíz del proyecto:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

La interfaz está disponible en [http://127.0.0.1:5173](http://127.0.0.1:5173). La conexión se establece mediante el campo **Credencial del operador** y el botón **Conectar**. Ambos servicios deben permanecer en ejecución. `Ctrl+C` detiene el servicio de la terminal correspondiente.

## Funcionamiento de la simulación

Las compras reciben un importe en USDT y las ventas una cantidad de BTC. Cada operación nueva consulta el ticker público de MEXC; el precio utilizado puede diferir del mostrado previamente en el dashboard.

La contabilidad utiliza aritmética decimal. La cantidad de BTC se limita a ocho decimales y las compras se redondean hacia abajo. El importe sobrante permanece en efectivo. La simulación no aplica comisiones ni deslizamiento y no reproduce los mínimos de negociación del exchange.

El patrimonio se calcula como:

```text
Patrimonio = efectivo USDT + (cantidad BTC × precio BTC/USDT)
```

El tiempo máximo admitido desde el inicio de la consulta de precio hasta su registro es de diez segundos. El ticker no proporciona la fecha de la última negociación: las marcas temporales registradas corresponden a la consulta y recepción de la respuesta. La última vela puede estar en formación.

Cuando el mercado no está disponible, las operaciones nuevas se bloquean. El efectivo y el historial permanecen accesibles; la valoración actual se devuelve como no disponible. La interfaz identifica las lecturas vencidas o sin conexión confirmada.

Los reintentos con el mismo identificador y contenido devuelven la operación original. Una respuesta interrumpida puede corresponder a una operación ya registrada; el historial permite comprobar su resultado. Los identificadores pendientes del navegador no se conservan al recargar la página.

## Persistencia y seguridad

- Base de datos predeterminada: `backend/bot-v02.db`.
- Capital inicial aplicado una sola vez al crear la cuenta.
- Actualización de saldos e historial en una misma transacción SQLite.
- Base independiente de V0.1, sin migración automática de `bot-v01.db`.
- Todas las rutas `/api/*` requieren el encabezado `X-API-Key`.
- Credencial del operador conservada únicamente en memoria del navegador y nunca enviada a MEXC.
- Archivos `.env`, bases de datos y dependencias instaladas excluidos del control de versiones.
- Ejecución local con un solo proceso del backend.

Los controles manuales comprueban saldo, posición, precisión y vigencia del precio. Los límites experimentales de exposición y pérdida diaria de V0.1 no forman parte del flujo manual V0.2.

## API

| Método y ruta | Función |
|---|---|
| `GET /api/state` | Saldos, cotización, patrimonio y últimas 100 operaciones |
| `GET /api/candles` | Últimas 60 velas de un minuto |
| `GET /api/history?limit=100&offset=0` | Historial paginado, hasta 500 registros por consulta |
| `POST /api/trades` | Registro de compra o venta simulada |

El cuerpo de una operación contiene `request_id` en formato UUID, `side` con valor `buy` o `sell`, y `amount` como texto decimal. El servidor obtiene el precio; no acepta un precio impuesto por el cliente.

Respuestas de error principales: `401` para autenticación, `422` para formato inválido, `409` para conflictos o restricciones de la operación y `503` para indisponibilidad del mercado o la persistencia.

El esquema de la API está disponible en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Pruebas

Desde `backend`:

```powershell
..\..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Desde `frontend`:

```powershell
npm test
npm run build
```

La verificación automatizada de V0.2 registró 28 pruebas backend y cuatro pruebas frontend aprobadas, además de la compilación TypeScript/Vite. Las pruebas backend utilizan respuestas de mercado controladas y bases temporales. Las pruebas frontend cubren lógica y comprobaciones estáticas; no montan componentes Vue.

La validación manual local confirmó la visualización del mercado, compras y ventas simuladas, rechazo de operaciones con saldo insuficiente y recuperación de saldos e historial tras reiniciar el backend.

## Alcance

V0.2 es una aplicación académica de operaciones manuales simuladas. No incluye órdenes reales, apalancamiento, posiciones cortas, modelo predictivo ni decisiones automáticas mediante LLM. Los resultados de la simulación no constituyen una evaluación de rentabilidad de una estrategia.

La publicación del código en GitHub no despliega los servicios. FastAPI y SQLite requieren un entorno de ejecución; GitHub Pages por sí solo no ejecuta el backend.

## Referencia

[Documentación oficial de MEXC Spot](https://mexcdevelop.github.io/apidocs/spot_v3_en/): endpoints públicos de precios y velas.
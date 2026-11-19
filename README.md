# Bot de Trading · V0.1

Prototipo de bot de trading con interfaz en **Vue 3**, API en **FastAPI** y simulación **Paper** para BTCUSDT. Incluye un modo de demostración independiente del backend y un ciclo experimental de consulta de mercado, propuesta de decisión, control de riesgo y registro de operaciones simuladas.

**Versión:** 0.1.0

## Estado del proyecto

La interfaz compila correctamente y la conexión con la API ha sido verificada. El backend consulta datos públicos de MEXC y dispone de un adaptador preliminar para Ollama local. La integración de la API privada del LLM y del modelo predictivo con su escalador sigue pendiente.

El pronóstico actual utiliza una referencia de rendimiento igual a cero. El proyecto no envía órdenes reales ni realiza retiros. La simulación utiliza el último cierre conocido como precio de referencia; sus resultados no constituyen un backtest ni una medición de rentabilidad.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Interfaz | Vue 3, TypeScript y Vite |
| Backend | Python, FastAPI y httpx |
| Persistencia | SQLite |
| Datos de mercado | API pública de velas diarias de MEXC |
| LLM experimental | Ollama local, modelo `llama3.2` |
| Pruebas | unittest y ejecutor de pruebas de Node.js |

## Funcionalidades

- Visualización del activo, la conexión y el estado de ejecución.
- Consulta de efectivo, posición y patrimonio en USDT para BTCUSDT.
- Última vela, rendimiento diario, distancia a SMA20 y volatilidad de 20 rendimientos.
- Presentación separada del pronóstico de referencia, la propuesta del LLM, la acción final y el motivo del control de riesgo.
- Historial de decisiones y mensajes de error.
- Controles para iniciar, pausar y detener el ciclo.
- Demostración con datos ficticios, sin solicitudes al backend.

Las fechas se muestran en UTC. Si se pierde la conexión, la interfaz conserva la última lectura y la marca como no confirmada. Cambiar al modo demostración o cerrar la página no detiene el backend.

## Arquitectura

```text
Vue 3 + TypeScript
        |
        v
FastAPI — autenticación del operador
        |
        v
MEXC — velas diarias, validación e indicadores
        |
        v
Pronóstico de referencia → Ollama local → validación de JSON
                                              |
                                              v
                                     Reglas de riesgo
                                              |
                                              v
                                     Registro Paper → SQLite
```

El LLM propone una acción; las reglas de saldo, posición y riesgo se aplican en Python. La respuesta JSON debe incluir acción, símbolo, fecha de vela y una justificación breve. El símbolo y la fecha deben coincidir con la consulta.

SQLite conserva el estado por símbolo y las decisiones por símbolo y vela. El backend admite un único proceso.

## Estructura del repositorio

```text
bot-trading-v0.1/
├── backend/
│   ├── core.py
│   ├── main.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   ├── tests/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.10 o posterior.
- Node.js 22.13 o posterior y npm.
- Acceso a Internet para instalar dependencias y consultar MEXC.
- Ollama con un modelo local para ejecutar el ciclo experimental con LLM.

La demostración de la interfaz no necesita backend, claves ni acceso a MEXC. Consultar el estado de la API tampoco requiere Ollama.

## Ejecución en Windows PowerShell

### 1. Iniciar la interfaz

Desde la raíz del proyecto:

```powershell
cd frontend
npm install
npm run dev
```

Abre `http://127.0.0.1:5173`. La aplicación inicia en modo demostración: los controles modifican el estado visual y los datos de ejemplo permanecen fijos.

### 2. Preparar el backend

En otra terminal, desde la raíz del proyecto:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
```

Copia la plantilla solo durante la configuración inicial para conservar los valores de un archivo `.env` existente.

Genera una clave de operador:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

Guarda el valor generado en `OPERATOR_API_KEY` dentro de `backend/.env`. Mantén `LLM_API_KEY` vacío salvo que utilices un gateway local que lo requiera.

### 3. Iniciar la API y conectar la interfaz

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

En la interfaz, introduce la clave de operador y selecciona **Conectar**. El backend inicia detenido. El botón **Iniciar** activa el ciclo experimental y requiere que los servicios de mercado y LLM estén disponibles.

Durante el desarrollo, Vite redirige las solicitudes a `/api` hacia el backend local.

### 4. Preparar Ollama para el ciclo experimental

Con Ollama instalado:

```powershell
ollama pull llama3.2
ollama serve
```

Ejecuta `ollama serve` solo si el servicio no está iniciado. El adaptador utiliza el contrato `/api/chat` y requiere inferencia local. La futura API privada necesitará su propia adaptación y pruebas de integración.

## Claves y seguridad

- **`OPERATOR_API_KEY`** protege la consulta de estado y los comandos del bot. Se introduce en la interfaz y se conserva temporalmente en memoria, sin usar `localStorage` ni `sessionStorage`.
- **`LLM_API_KEY`** es una credencial independiente. Permanece en el backend y solo se envía como cabecera a un gateway local compatible; nunca se introduce en la interfaz ni en el prompt.
- La configuración local se guarda en `backend/.env`, excluido de Git. `.env.example` debe contener únicamente valores de ejemplo, sin credenciales reales.
- El adaptador acepta direcciones de bucle local y rechaza nombres de modelos que contengan `cloud`. Debe utilizarse con un servicio y un modelo que ejecuten inferencia local.
- Ollama local no exige autenticación por defecto. Si se utiliza un gateway, este debe validar la credencial configurada.
- Los eventos no guardan claves, cabeceras ni respuestas completas de servicios externos.

La configuración está orientada al uso local. Para exponer los servicios por red se requiere configurar HTTPS y revisar los controles de acceso. Si una clave se comparte por error, debe sustituirse.

## Simulación Paper

El capital inicial es de **50,000 USDT** y el costo configurado para la simulación es de **0.0%**.

- No se admite apalancamiento, posiciones negativas ni compras superiores al efectivo disponible.
- `MAX_EXPOSURE` limita el importe de una nueva compra; no realiza rebalanceo continuo.
- La pérdida diaria se mide en UTC a partir de la última valoración guardada al comenzar el día observado. El bloqueo se mantiene durante ese día y se evalúa en cada ciclo.
- Pausar o detener invalida el ciclo pendiente antes de registrar una operación. Detener no liquida la posición.
- La decisión y el estado se guardan en una misma transacción. Al reiniciar se recupera el estado persistido y el bot permanece detenido.
- Cada combinación de símbolo y vela puede registrarse una sola vez.

Se guardan por separado la fecha de la vela y la fecha de la decisión. Quedan pendientes la ejecución posterior a la señal, los mínimos y la precisión del par, el deslizamiento y el registro detallado de órdenes.

La base de datos se crea en `backend/bot-v01.db`. No hay migración automática desde una base anterior llamada `bot.db`.

## API

Todas las rutas siguientes requieren la cabecera `X-API-Key` con la clave del operador.

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/api/state` | Consultar el estado y los últimos registros |
| `POST` | `/api/start` | Activar el ciclo experimental |
| `POST` | `/api/pause` | Pausar e invalidar el ciclo pendiente |
| `POST` | `/api/stop` | Detener sin liquidar la posición |

Las claves vacías o incorrectas reciben una respuesta HTTP 401. Con el backend en ejecución, la documentación interactiva está disponible en `http://127.0.0.1:8000/docs`.

## Pruebas y compilación

Para ejecutar las pruebas del backend, desde `backend` y con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas de reglas utilizan la biblioteca estándar de Python. Las pruebas de API necesitan las dependencias del backend; si faltan, se omiten.

Para ejecutar las pruebas de lógica y compilar la interfaz, desde `frontend`:

```powershell
node --test tests/logic.test.mjs
npm run build
```

Las pruebas de lógica utilizan funciones reactivas y solicitudes de red simuladas; no montan componentes Vue. La compilación genera los archivos de la interfaz en `frontend/dist`.

## Próximos pasos

- Integrar la API privada del LLM y validar su contrato, manteniendo inferencia local y credenciales fuera del prompt.
- Incorporar el modelo predictivo y su escalador, con versiones y variables de entrada definidas.
- Completar el motor Paper con ejecución posterior a la señal, precisión, mínimos, costos y deslizamiento.
- Ampliar el registro de órdenes y las pruebas de integración de mercado, LLM y controles de riesgo.
- Registrar ciclos completos y comparar el modelo sin LLM, el agente con LLM y la estrategia de comprar y mantener con métricas equivalentes.

## Despliegue

La ejecución local requiere mantener activos el frontend y el backend; el ciclo experimental también necesita Ollama. La compilación del frontend puede servirse como contenido estático, pero requiere configurar el acceso a la API. GitHub Pages por sí solo no ejecuta FastAPI ni Ollama.

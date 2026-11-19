# Bot de Trading · V0.1

**Versión:** 0.1.0  
**Fecha de revisión:** 17 de noviembre de 2026  
**Asignatura:** Ciencia de datos aplicada a la economía  
**Estado:** prototipo de interfaz y backend preliminar; sin órdenes reales.

## Objetivo y alcance

Esta primera versión presenta la interfaz del bot de trading, su estructura de comunicación y controles iniciales. Se toma como referencia la pizarra del 17 de noviembre: entrega V0.1, repositorio público, versión y tecnologías en el README, uso de un LLM local y protección de las credenciales.

La interfaz utiliza **Vue 3, TypeScript y Vite**, tecnologías recomendadas en la pizarra. Se eligió **MEXC** entre las plataformas mencionadas. El protocolo PDF especifica React para el proyecto final; esta V0.1 conserva la recomendación de Vue de la actividad presencial. La decisión tecnológica para la entrega final queda sujeta al criterio de evaluación de esa etapa.

El modo demostración funciona sin backend y muestra datos ficticios identificados. El backend contiene un ciclo experimental de consulta, validación, propuesta y registro Paper. El pronóstico es una **referencia igual a cero**, sin modelo entrenado conectado. La API privada del profesor está pendiente de recepción e integración; no se supone que tenga el mismo contrato que el adaptador actual de Ollama.

## Tecnologías aplicadas

| Componente | Tecnología y alcance |
|---|---|
| Interfaz | Vue 3, TypeScript y Vite |
| Backend | Python, FastAPI y httpx |
| Persistencia | SQLite; estado por símbolo y decisiones por símbolo/vela |
| Mercado | API pública de velas diarias de MEXC |
| LLM | Adaptador preliminar para Ollama local |
| Pronóstico | Referencia cero; integración del modelo y escalador pendiente |
| Verificación | unittest y pruebas aisladas con Node.js |

Las dependencias declaradas conservan las familias de versiones del prototipo original. Su instalación completa, auditoría y bloqueo reproducible de versiones están pendientes; no se declara una revisión de vulnerabilidades aprobada.

## Estructura

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
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/
│   ├── REVISION_V0.1.md
│   └── VERIFICACION.md
├── .env.example
├── .gitignore
└── README.md
```

## Interfaz

- Activo, estado de conexión y estado de ejecución.
- Efectivo, posición y patrimonio expresado en USDT para BTCUSDT.
- Última vela, rendimiento diario, distancia a SMA20 y volatilidad de 20 rendimientos.
- Pronóstico identificado como referencia cero.
- Propuesta del LLM, acción final y motivo del control de riesgo por separado.
- Historial de decisiones y mensajes de error.
- Controles de inicio, pausa y detención.
- Modo demostración explícito, sin solicitudes al backend.

Una desconexión conserva la última lectura y marca el estado como no confirmado. No se reemplazan datos del servidor por ejemplos. Las fechas se muestran en UTC. Cambiar a demostración o cerrar la página no detiene el backend.

## Arquitectura preliminar

```text
Vue + TypeScript → FastAPI autenticado → MEXC → validación e indicadores
                                             ↓
                          referencia cero → Ollama local
                                             ↓
                         validación JSON → riesgo → registro Paper → SQLite
```

El LLM solo propone. Las reglas de saldo, posición y riesgo se ejecutan en Python. El contrato JSON exige acción, símbolo, fecha de vela y justificación breve. El símbolo y la fecha deben coincidir con la consulta.

## Seguridad

- `LLM_API_KEY` permanece en el backend. Solo se utiliza como cabecera hacia un gateway local compatible; no se incluye en el prompt ni en el frontend.
- `OPERATOR_API_KEY` es una credencial distinta, destinada al acceso del operador. Protege tanto `/api/state` como los comandos. Se introduce en la interfaz y permanece temporalmente en memoria; no se guarda en `localStorage` ni `sessionStorage`.
- `.env.example` contiene nombres y valores de configuración sin claves reales. La configuración local se guarda en `backend/.env`, excluido de Git.
- El adaptador permite únicamente direcciones de bucle local y rechaza nombres de modelos que contengan `cloud`. Estos filtros no sustituyen la verificación de que el servicio y el modelo ejecutan inferencia local.
- Ollama local no exige autenticación por defecto. La existencia de una cabecera `Authorization` no demuestra que el servicio valide la clave. El gateway privado y sus pruebas quedan pendientes de integración.
- No existen llamadas a endpoints de órdenes reales, retiros o negociación autenticada de MEXC.
- Los eventos no almacenan cabeceras, claves ni respuestas completas de servicios externos.

El prototipo se ejecuta únicamente en el equipo local. Un despliegue accesible por red requiere revisar autenticación, HTTPS y control de acceso. Publicar el código en GitHub no equivale a desplegar los servicios.

## Reglas y limitaciones de Paper

El capital inicial es de **50,000 USDT** y el costo académico es **0.0%**, según la sección 15 del protocolo del agente. Estas cifras no representan una afirmación sobre tarifas vigentes de MEXC.

- Sin apalancamiento, posiciones negativas ni compras por encima del efectivo.
- `MAX_EXPOSURE` limita el importe de una nueva compra; no implementa rebalanceo continuo cuando cambia el precio.
- La pérdida diaria se mide en UTC con la última valoración guardada al iniciar el día observado. El bloqueo se conserva durante ese día. La supervisión depende de las observaciones del ciclo; no es un control intradía continuo.
- Pausar y detener invalidan el ciclo pendiente antes de registrar una operación. Detener no liquida la posición.
- Decisión y estado se guardan en una misma transacción. Al reiniciar se recuperan efectivo, posición, valoración, último registro y base diaria, con el bot detenido.
- Cada símbolo y vela puede registrarse una sola vez. Se admite un único proceso del backend.

La simulación conserva un **precio de referencia correspondiente al último cierre conocido**. Se registra por separado la fecha de la vela y la fecha de la decisión. No se interpreta ese cierre pasado como un precio de ejecución disponible tras consultar al LLM. La ejecución temporalmente válida, mínimos, precisión del par, deslizamiento y registro detallado de órdenes quedan pendientes. El patrimonio del prototipo no constituye evidencia de rentabilidad ni un backtest válido.

La base nueva se llama `backend/bot-v01.db`; no migra automáticamente una base `bot.db` del prototipo anterior. El historial anterior no forma parte de este paquete.

## Ejecución local

Requisitos: Python 3.10 o posterior, Node.js 22.13 o posterior y npm. Ollama solo es necesario para probar el ciclo experimental. La demostración de interfaz no necesita claves ni acceso a MEXC.

### Interfaz de demostración

Desde la raíz del proyecto:

```powershell
cd frontend
npm install
npm run dev
```

Dirección local: `http://127.0.0.1:5173`. La aplicación inicia en demostración. Los botones cambian únicamente el estado visual y mantienen fijos los datos de ejemplo.

### Backend en Windows PowerShell

En otra terminal, desde la raíz del proyecto:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
```

Antes de iniciar el backend, `backend/.env` requiere una credencial propia en `OPERATOR_API_KEY`. Una cadena aleatoria puede generarse localmente con:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

Ese valor se utiliza únicamente para el acceso del operador. `LLM_API_KEY` permanece vacío mientras no exista un gateway configurado que lo requiera. La credencial privada del LLM no se introduce en la interfaz.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

La interfaz permite introducir la credencial del operador y seleccionar **Conectar**. El backend inicia detenido. La consulta del estado no necesita Ollama; **Iniciar** activa el ciclo experimental y sí necesita las dependencias externas disponibles.

### Backend en macOS o Linux

Desde la raíz del proyecto:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp ../.env.example .env
```

Después de configurar `backend/.env`:

```bash
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
```

### Ollama local, integración experimental

El adaptador utiliza el modelo `llama3.2` y el contrato `/api/chat`. La preparación local, con Ollama instalado, contempla:

```text
ollama pull llama3.2
ollama serve
```

`ollama serve` solo es necesario cuando el servicio no está iniciado. El modelo descargado debe ejecutar inferencia local. La evidencia de modelo, versión, hardware y latencia está pendiente. Una API posterior con otro formato requiere adaptar y probar el conector.

## API del backend

| Método y ruta | Función | Acceso |
|---|---|---|
| `GET /api/state` | Estado y últimos registros | `X-API-Key` del operador |
| `POST /api/start` | Activación del ciclo | `X-API-Key` del operador |
| `POST /api/pause` | Pausa e invalidación del ciclo pendiente | `X-API-Key` del operador |
| `POST /api/stop` | Detención sin liquidación | `X-API-Key` del operador |

La descripción automática de las rutas se encuentra en `http://127.0.0.1:8000/docs`. La API rechaza claves vacías o incorrectas con HTTP 401. El proxy de Vite conecta `/api` con el backend local durante el desarrollo; no constituye configuración de producción. GitHub Pages por sí solo no ejecuta FastAPI ni Ollama.

## Verificación

Desde `backend`:

```text
python -m unittest discover -s tests -v
```

Las pruebas de API requieren las dependencias instaladas; de lo contrario se identifican como omitidas. Las pruebas de reglas usan la biblioteca estándar.

Desde `frontend`:

```text
node --test tests/logic.test.mjs
npm run build
```

Las pruebas aisladas de interfaz usan dobles de las funciones reactivas y de red; no montan componentes Vue. La compilación y la inspección visual se verifican por separado.

Los resultados de esta revisión y las limitaciones del entorno están en [docs/VERIFICACION.md](docs/VERIFICACION.md). El análisis de requisitos y correcciones se encuentra en [docs/REVISION_V0.1.md](docs/REVISION_V0.1.md).

## Pendientes de la siguiente versión

1. Integración y pruebas de la API privada del profesor, manteniendo inferencia local y credenciales fuera del prompt.
2. Carga del modelo predictivo y escalador aprobados, con versiones y contrato de variables.
3. Motor Paper con ejecución posterior a la señal, precisión, mínimos y deslizamiento documentados.
4. Registro de órdenes y costos, bitácora completa y pruebas de los nueve escenarios del protocolo.
5. Evidencia de 20 ciclos válidos, separando replay de conexión actual.
6. Comparación modelo sin LLM, agente con LLM y comprar y mantener, con métricas equivalentes.
7. Compilación y revisión visual completas, pruebas de integración, auditoría de dependencias y archivos de bloqueo.
8. Publicación del repositorio y registro de su URL y commit de entrega.

## Referencias

- Pizarra de la actividad del 17 de noviembre de 2026.
- Protocolo de Deep Learning para Finanzas, secciones 14, 15 y 16.
- [MEXC: velas y datos de mercado](https://mexcdevelop.github.io/apidocs/spot_v3_en/#kline-candlestick-data).
- [Ollama: autenticación](https://docs.ollama.com/api/authentication).
- [Vite: opciones del servidor de desarrollo](https://vite.dev/config/server-options.html#server-proxy).

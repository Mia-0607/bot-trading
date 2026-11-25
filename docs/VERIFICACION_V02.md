# Verificación V0.2 · 24 de noviembre de 2026

## Backend

`python -m unittest discover -s tests -v`: **28 pruebas aprobadas**, ninguna omitida.

Incluye 17 pruebas conservadas de `core.py` V0.1 y 11 pruebas nuevas de API/contabilidad V0.2: autenticación de las cuatro rutas, compra/venta, persistencia tras reinicio, UUID idempotente, rechazo de importes inválidos, saldo insuficiente, precio impuesto por el cliente, caídas MEXC, precios inválidos, cotización vencida, validación OHLC, ausencia de inicio automático, precisión decimal, rollback y gasto concurrente sin sobregiro.

Las respuestas MEXC en estas pruebas son dobles controlados. Se usan bases temporales, no bases de la usuaria.

## Frontend

`npm test`: **4 pruebas aprobadas**. Cubren importes, caducidad, coordenadas de gráfica plana y comprobaciones estáticas de protección/simulación. No montan Vue ni equivalen a una prueba de clics en navegador.

`npm run build`: **aprobado**, incluyendo comprobación TypeScript con `vue-tsc` y compilación Vite. Se reutilizaron las dependencias ya instaladas de V0.1; la descarga limpia `npm ci` no quedó verificada en este entorno. Se conserva el archivo de bloqueo con la versión del proyecto actualizada.

Entorno de verificación: Python 3.12 y Node 26.8.1. Las versiones mínimas documentadas no se probaron en una matriz independiente.

## Consulta real a MEXC

Intentada desde el backend, pero bloqueada por resolución DNS en el entorno de ejecución (`getaddrinfo failed`). **No se declara una conexión real exitosa**. Se consultó la documentación oficial de endpoints públicos. Debe completarse la comprobación manual indicada en README desde el equipo con acceso a MEXC.

La inspección visual y las compras/ventas mediante clics en navegador quedan pendientes. Compilar no certifica esa inspección.

## Archivos y entrega

V0.1 de OneDrive se leyó sin modificarla. El paquete V0.2 se preparó en la carpeta de entregables de Codex porque esta sesión no tiene permiso de escritura en OneDrive. Se excluyeron `.env`, bases personales, `.git`, dependencias instaladas y archivos temporales del ZIP.

No se ejecutaron órdenes reales, llamadas al LLM, commit ni push a GitHub. Las carpetas `legacy_v01` y documentos V0.1 son referencias históricas, no el servidor activo.

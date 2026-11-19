# Registro de verificación · V0.1

**Fecha:** 17 de noviembre de 2026.

## Resultados observados

| Verificación | Resultado |
|---|---|
| Pruebas de reglas y validación de datos | 17 aprobadas. Ejecutadas con Python 3.12. |
| Pruebas aisladas de lógica de interfaz | 7 aprobadas. Ejecutadas con Node.js 26.8.1. |
| Pruebas de API | 5 omitidas por falta de FastAPI, httpx y python-dotenv en el entorno. Se incluyen en el proyecto; no se contabilizan como aprobadas. |
| Instalación de dependencias Python | Bloqueada por resolución de red al consultar el índice de paquetes. |
| Instalación de dependencias frontend | Bloqueada por `ENOTFOUND` al consultar `registry.npmjs.org`. |
| Compilación completa con Vue/TypeScript/Vite | Pendiente: dependencias no instaladas. |
| Navegación e inspección visual de la aplicación | Pendientes. |
| Conexión real con MEXC y Ollama | No ejecutada. |
| API privada del profesor | Pendiente de recepción e integración. |
| Publicación en GitHub | No realizada. |

Las 24 pruebas aprobadas verifican componentes aislados; no acreditan una integración completa ni sustituyen las pruebas de aceptación del protocolo.

## Cobertura de las pruebas ejecutadas

**Reglas de backend:** exclusión de velas abiertas, conservación de la última vela cerrada, conjunto vacío, fechas duplicadas, huecos, precios inválidos, dimensiones incorrectas, historia insuficiente, datos atrasados, indicadores en serie constante, límites de configuración, contrato JSON, compra limitada por saldo y exposición, rechazo de recompra o venta sin posición, bloqueo al alcanzar pérdida máxima, cambio de base diaria y venta con actualización de patrimonio.

**Lógica de interfaz:** demostración sin red, conexión fallida sin conversión a demo, conservación de la última lectura, rechazo de credencial, validación de respuestas, fallo de comando sin confirmación falsa y eliminación de la credencial al volver a demo.

Las pruebas de interfaz extraen la lógica TypeScript y utilizan dobles de las funciones reactivas y de red. No montan Vue, no ejecutan su compilador y no evalúan diseño visual o accesibilidad completa.

## Pruebas de API preparadas y pendientes

1. Protección de consulta y comandos con credencial del operador.
2. Detención durante la espera al LLM sin registrar una operación.
3. Detención seguida de inicio sin reutilizar el ciclo anterior.
4. Procesamiento único de una vela y recuperación del estado tras reinicio.
5. Reversión transaccional ante una escritura fallida.

Estas pruebas simulan las dependencias externas. Incluso después de aprobarlas, permanecen necesarias las pruebas con MEXC, el servicio local y la API privada efectivamente configurados.

## Ejecución reproducible

Desde `backend`:

```text
python -m unittest discover -s tests -v
```

Desde `frontend`:

```text
node --test tests/logic.test.mjs
npm install
npm run build
```

La prueba de lógica requiere Node.js 22.13 o posterior por la función de eliminación de tipos utilizada. El frontend no se considera compilado por el solo resultado de esa prueba.

## Pendientes de aceptación

- Instalar las dependencias en un entorno con acceso a los registros de paquetes.
- Ejecutar las cinco pruebas de API sin omisiones y conservar la salida.
- Compilar el frontend y revisar las vistas de escritorio y móvil.
- Verificar la inferencia local y la autenticación del gateway con claves ausentes, incorrectas y válidas.
- Demostrar los escenarios de error restantes y los ciclos requeridos en la etapa final.
- Incorporar los archivos de bloqueo obtenidos de una instalación verificada y la revisión de dependencias.
- Revisar el contenido preparado para Git y registrar la URL y commit público de entrega.

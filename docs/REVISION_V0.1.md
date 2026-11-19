# Revisión técnica y de alcance · Bot de Trading V0.1

**Fecha:** 17 de noviembre de 2026  
**Versión revisada:** 0.1.0  
**Objeto:** primera entrega de interfaz y estructura preliminar del bot.

## Criterio de revisión

La pizarra define el alcance inmediato de la V0.1. El protocolo PDF establece los requisitos de la práctica y del agente final, que se registran como referencia para las etapas posteriores. Esta entrega no declara un agente terminado ni resultados de rentabilidad.

La imagen de la pizarra recomienda TypeScript, Vite y Vue para la interfaz. Por ello, el uso de Vue es coherente con esta actividad. La exigencia de React en las páginas 13 y 15 del PDF sigue siendo una diferencia documental para la etapa final, no un motivo para sustituir Vue en esta versión.

## Requisitos de la pizarra

| Requisito | Evidencia y estado |
|---|---|
| Entrega V0.1 del bot de trading | Código y documentación identificados como versión 0.1.0; prototipo de interfaz. |
| Git público | Paquete preparado para repositorio. Publicación y URL pendientes; no se acredita visibilidad pública sin un repositorio verificable. |
| Versión y tecnologías en README | Incluidas con el alcance real de cada componente. |
| TypeScript, Vite y Vue para UI | Aplicados en el frontend, conforme a la recomendación. Compilación completa pendiente. |
| Opciones Polymarket o MEXC | Se utiliza MEXC como fuente pública. No se requiere implementar ambas plataformas. |
| Consumo de LLM local | Adaptador a Ollama local presente; ejecución y evidencia de inferencia local pendientes. |
| No pasar API a IA | Interpretado como protección de credenciales: la clave del LLM no entra al prompt ni al frontend. La autenticación privada queda pendiente de integración. |

## Correcciones incorporadas

### Interfaz y comunicación

- Separación explícita entre demostración y conexión con el servidor. El modo demo no emite comandos de red.
- Conservación de la última lectura ante desconexión, con aviso de posible desactualización y estado sin confirmar.
- Manejo de errores de red, tiempos de espera y respuestas no válidas.
- Bloqueo de comandos simultáneos y mensajes de confirmación diferenciados de los fallos.
- Distinción entre propuesta del LLM, acción final y motivo de rechazo. Mantener posición se distingue de permanecer en efectivo.
- Pronóstico identificado como referencia cero, sin atribuirlo a un modelo entrenado.
- Fechas en UTC y valores del par BTCUSDT expresados en USDT, evitando presentarlos como dólares estadounidenses.
- Etiqueta del campo de acceso, mensajes accesibles y estilos de foco para navegación por teclado.

### Backend y persistencia

- Invalidación del ciclo en curso al pausar o detener, también cuando ocurre una secuencia detener–iniciar mientras se espera al LLM.
- Comprobación final del estado inmediatamente antes de la transacción, sin una espera intermedia.
- Recuperación del estado completo: efectivo, cantidad, patrimonio, última decisión, referencia diaria y bloqueo de riesgo. El arranque siempre queda detenido.
- Identificación de decisiones mediante símbolo y fecha de vela.
- Escritura transaccional del estado y la decisión para evitar cambios de saldo sin registro confirmado.
- Inicio y cierre controlados de la tarea del backend.
- Uso de un solo proceso documentado. No se acredita soporte para múltiples trabajadores ni ejecución distribuida.

### Validación y controles

- Validación de suficientes cierres, dimensiones, fechas, frecuencia diaria, duplicados, huecos y precios positivos y finitos.
- Selección de velas cerradas mediante su fecha de cierre, sin eliminar automáticamente la última fila.
- Revisión de antigüedad del dato antes y después de la consulta al LLM.
- Validación de los rangos de exposición y pérdida máxima.
- Actualización de la base de pérdida por día UTC y conservación del bloqueo durante ese día.
- Validación del objeto JSON del LLM, acción permitida, símbolo, fecha y justificación.

### Seguridad y documentación

- Autenticación en consulta de estado y comandos.
- Eliminación del almacenamiento persistente de la credencial del operador. Su permanencia temporal en memoria se documenta sin confundirla con la clave del LLM.
- Mensajes de error controlados, sin volcar secretos, cabeceras o respuestas completas al registro.
- Configuración local cargada desde una ruta estable.
- Ampliación de `.gitignore` para entornos virtuales, variantes de `.env`, bases auxiliares y archivos generados.
- Eliminación de la exclusión global de modelos `.pt` y escaladores `.joblib`, que podrán formar parte de una entrega posterior aprobada.
- Corrección de afirmaciones del README que presentaban autenticación privada, modelo o integración completa como terminados sin evidencia.
- Instrucciones separadas para interfaz, backend y servicio local; distinción entre repositorio público y despliegue.

## Límites que permanecen abiertos

| Aspecto | Situación de la V0.1 y trabajo pendiente |
|---|---|
| Modelo predictivo | Referencia cero. Faltan modelo, escalador, versión, contrato de variables y evidencia vinculada a los avances. |
| API privada del LLM | La cabecera de autenticación está prevista; el gateway que la valida y la API del profesor no están integrados. |
| Inferencia local | Se restringe la dirección del adaptador a bucle local. Falta demostrar que el servicio ejecuta un modelo local, con versión, hardware y latencia. |
| Ejecución Paper | Registro didáctico al último cierre. Faltan ejecución posterior a la señal, precisión, mínimos y deslizamiento. No es un backtest válido. |
| Exposición | Límite de nuevas compras; falta definir y probar la política ante una exposición que aumente por variación del precio. |
| Pérdida diaria | Se calcula con valoraciones disponibles en el ciclo. No hay supervisión intradía continua. |
| Riesgo y detención | El código incorpora las correcciones; las pruebas del backend con FastAPI instalado permanecen pendientes en esta revisión. |
| Registro completo | Existen decisiones, estado y eventos. Faltan órdenes detalladas y bitácora con causa, corrección y verificación. |
| Nueve escenarios del protocolo | Hay pruebas parciales de reglas y pruebas de API preparadas. No se declara la demostración completa de los nueve escenarios. |
| Evaluación final | Faltan 20 ciclos válidos, comparaciones de estrategias y métricas de rendimiento, drawdown, Win Rate y latencia. |
| Reproducibilidad | Faltan instalación limpia completa, archivos de bloqueo y auditoría de dependencias. |
| Publicación | No se realizó publicación en GitHub ni despliegue de servicios. |

## Precisiones sobre el protocolo

Para el agente, la página 14 establece 50,000 unidades cotizadas y costo de 0.0%; esos valores se conservan. La práctica de simulación anterior utiliza 100,000 y 0.10% por operación. Son apartados distintos y no se mezclan sus supuestos.

El documento contiene una diferencia adicional: la página 1 menciona rentabilidad de +20% y superioridad frente a regresión lineal, mientras que las páginas 10, 13 y 15 no exigen ganancias o mejora del modelo sencillo para los criterios allí descritos. Esa diferencia se registra para definición académica posterior. Esta V0.1 no presenta rentabilidad ni superioridad predictiva como resultados.

## Prioridades antes de declarar la entrega verificada

1. Completar instalación, compilación del frontend y revisión visual en escritorio y móvil.
2. Ejecutar las pruebas de API y verificar detención durante una consulta, reinicio, clave inválida y transacciones fallidas.
3. Confirmar el contenido que se incorpora a Git: sin `.env`, claves, bases locales, dependencias ni resultados de ejemplo presentados como reales.
4. Registrar versiones efectivamente instaladas y resolver la auditoría de dependencias.
5. Publicar el repositorio y registrar URL y commit de la V0.1.

Las integraciones del modelo, gateway privado y motor Paper completo corresponden a la siguiente etapa. La aceptación académica de la V0.1 depende de la revisión del docente y del alcance definido para esta entrega.

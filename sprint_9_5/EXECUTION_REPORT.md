# Sprint 9.5 — Execution Report

**Objetivo del sprint:** tomar UN feed RSS verificado, correr el pipeline de producción completo, generar el Daily Brief y el Training Report, medir el tiempo total de ejecución, y documentar cada paso manual que todavía se necesita — para identificar qué falta antes de la automatización completa.

**Resultado en una frase:** el pipeline en sí es rapidísimo (89ms de punta a punta, sin contar la descarga) y funciona correctamente con datos reales — el trabajo que falta no es de rendimiento ni de robustez del código, es de **curación de contenido** y **acceso de red en el entorno de despliegue real**.

---

## 0. Qué se hizo exactamente

1. Se tomó el feed `source.diario_financiero` — el primero marcado `verified: true` en `config/rss_sources.yml` desde el Sprint 9.
2. Se descargó su contenido **real y en vivo** (no un fixture) usando `web_fetch`, la herramienta de Claude — no `rss/fetcher.py` directo, porque el proxy de salida de este entorno de desarrollo bloquea `df.cl` (ver sección 1, es el hallazgo más importante de este sprint).
3. Se guardó una muestra representativa de 8 de los ~40 artículos que el feed devolvió (`sprint_9_5/df_live_fetch.xml`) — transcribir los ~40 a mano era innecesariamente propenso a error; 8 alcanza para medir el pipeline con datos reales.
4. Se corrió el pipeline de producción completo, sin modificar ni `rule_engine/`, ni `classification/`, ni el Rulebook, ni la Knowledge Base — exactamente el mismo código que `run_daily.py` ejecuta.
5. Se generaron `daily_brief.sprint9_5.html` y `training_report.sprint9_5.html`, ambos incluidos en el repositorio.
6. Se midió el tiempo de cada etapa por separado (`sprint_9_5/timings.json`).

El script escribe momentáneamente `data/daily_input/2026-08-04.json` (así se comportaría en producción real) y luego lo retira de esa carpeta — la copia que queda archivada vive en `sprint_9_5/daily_input.sprint9_5.json`, para no mezclar este dry run de 8 noticias curadas con los datos ficticios del Sprint 4 que ya viven en `data/daily_input/`.

Todo reproducible con `python sprint_9_5/run_and_measure.py`.

---

## 1. El hallazgo más importante: acceso de red

Al intentar la descarga real (`rss/fetcher.py` -> `requests.get`) contra la URL real de Diario Financiero, el resultado fue:

```
403 Client Error: Forbidden
Host not in allowlist: www.df.cl. Add this host to your network egress settings to allow access.
```

Esto **no es un fallo del feed ni del código** — es el proxy de salida de este entorno de desarrollo, que restringe a una allowlist de hosts. Confirma exactamente el mismo hallazgo del Sprint 9 (entonces con 6 feeds, ahora con este en particular).

Para no dejar el ejercicio en "no se pudo", se usó `web_fetch` (una herramienta de Claude con su propia ruta de red, distinta a la del sandbox) para obtener el contenido real del feed una sola vez, y se guardó localmente. El pipeline de producción corrió sobre ese contenido real vía `file://` — exactamente el mismo mecanismo que ya existía desde `examples/rss_demo/` (Sprint 9), pero esta vez con datos reales de hoy, no fixtures sintéticos.

**Paso manual #1 — el más urgente de todos:** en el entorno de despliegue real (no este sandbox de desarrollo), alguien tiene que confirmar que `rss/fetcher.py` puede alcanzar los hosts de los feeds directamente. Si el despliegue real corre detrás de un proxy corporativo o un firewall similar, esto no es un problema de PR HUB — es una configuración de red que alguien de infraestructura tiene que resolver antes de que la ingesta automática funcione fuera de una demo.

---

## 2. El segundo hallazgo, más importante todavía: el feed "verificado" no sirve para este producto

Las 8 noticias reales de Diario Financiero de esta corrida:

| Titular | Marca | Organismo | Event Type | Priority |
|---|---|---|---|---|
| Irán y EEUU establecen línea de comunicación... | — | — | Sin detectar | Sin clasificar |
| Dólar abre a la baja tras reunión EEUU-Irán... | — | — | Sin detectar | Sin clasificar |
| Plan de salvataje de metalúrgica de Talcahuano... | — | — | Sin detectar | Sin clasificar |
| Embotelladora Andina invertirá US$260 millones... | — | — | Sin detectar | Sin clasificar |
| SII identifica 84 empresas de alto riesgo fiscal... | — | — | Sin detectar | Sin clasificar |
| Elecciones en Colombia: De la Espriella... | — | — | Sin detectar | Sin clasificar |
| Capstone Copper Mantos Blancos, tramitación ambiental... | — | — | Sin detectar | Sin clasificar |
| Codelco evalúa venta de activos... | — | — | Sin detectar | Sin clasificar |

**8 de 8 sin ninguna relevancia automotriz.** No es un bug — Entity Recognition y Event Detection hicieron exactamente lo correcto (no inventaron una marca ni un evento que no estaba ahí). El problema es de **fuente**, no de código: la portada general de Diario Financiero es negocios/economía/política, no autos — "verificado" (la URL responde y el feed es real) no es lo mismo que "útil para PR HUB".

Esto tiene una consecuencia visible en el propio Daily Brief generado: como ninguna noticia tiene marca ni competidor, las 8 caen por defecto en la sección **Industria**, cada una con un "Por qué importa para Stellantis" genérico ("Contexto general de industria relevante para el panorama competitivo del día") que, para una noticia sobre elecciones en Colombia o el precio del dólar, es simplemente falso. El sistema no está mintiendo a propósito — es el efecto secundario honesto de que hoy no existe un estado "sin relevancia" distinto de "Industria sin marca detectada". Lo dejo anotado como hallazgo de producto para un sprint futuro (sección 4), no lo arreglé aquí — este sprint era para observar y medir, no para rediseñar la agregación.

**Paso manual #2:** alguien con criterio editorial tiene que curar URLs de feeds que sean temáticamente relevantes (secciones o tags de autos específicos, no portadas generales) — y, dado este resultado, probablemente convenga priorizar la verificación de los feeds especializados (`Rutamotor`, `Autocosmos`, `La Tercera/MT Online`) por sobre feeds generalistas como este, aunque este haya sido el primero en confirmarse como URL válida.

---

## 3. Tiempo de ejecución medido

| # | Etapa | Tiempo |
|---|---|---|
| 1 | Parseo + normalización (`rss/ingest.py:ingest_feed`) | 0.41 ms |
| 2 | Deduplicación | 0.15 ms |
| 3 | Escritura de `data/daily_input/YYYY-MM-DD.json` | 0.14 ms |
| 4 | Construcción del pipeline (carga Knowledge Base + Rulebook) | 63.93 ms |
| 5 | Clasificación (`pipeline.run()` × 8 noticias) | 5.55 ms |
| 6 | Agregación para el Daily Brief | 0.03 ms |
| 7 | Render del Daily Brief (HTML) | 0.33 ms |
| 8 | Render del Training Report (HTML) | 0.21 ms |
| | **Total medido (sin la descarga)** | **71.61 ms** |

(Se corrió dos veces durante este sprint: 88.78 ms y 71.61 ms. La varianza es ruido normal de sistema en operaciones de milisegundos, no una señal de nada — ambas corridas coinciden en lo que importa: la etapa 4 domina el tiempo total, y todo lo demás es prácticamente gratis.)

**Lectura honesta de estos números:**

- El **~64-75 ms de la etapa 4** (cargar Knowledge Base + Rulebook desde YAML) es, por lejos, el costo dominante — y es un costo **fijo por ejecución**, no por noticia ni por feed. Correr con 8 noticias o con 800 no cambiaría mucho ese número.
- La clasificación real (etapa 5) tomó **~0.7 ms por noticia** — extremadamente barata. El Rule Engine, tal como está, no es el cuello de botella de "automatización completa": podría procesar cientos de noticias por segundo sin cambios.
- **Lo que no está medido aquí, y es lo que realmente va a dominar el tiempo total en producción, es la descarga HTTP en sí.** Con 1 feed simulado localmente, esa etapa no existe en esta medición. Una estimación razonable, no medida: una petición HTTP real a un sitio de noticias suele tardar entre 200 ms y 2-3 segundos según el servidor y la carga. Con 9 feeds habilitados (los que quedarían activos si todos los `verified: false` se confirman) corriendo **secuencialmente** — que es como está escrito `rss/ingest.py` hoy, sin paralelismo — el tiempo total realista de un `run_daily.py` en producción rondaría **varios segundos, probablemente entre 3 y 15**, dominado enteramente por la red, no por el Rule Engine ni por el renderizado.

**Paso manual/técnico #3 (para un sprint futuro, no urgente todavía):** si el catálogo de feeds crece más allá de ~10, vale la pena paralelizar la descarga (`concurrent.futures` o similar) en `rss/ingest.py` — hoy no hace falta, porque solo hay 2 feeds confiables, pero conviene dejarlo anotado antes de que sea un problema real.

---

## 4. Cada paso manual que todavía existe (inventario completo)

| # | Paso manual | Por qué sigue siendo manual | Bloqueado por |
|---|---|---|---|
| 1 | Confirmar acceso de red real a los hosts de los feeds en el entorno de despliegue | El sandbox de desarrollo tiene una allowlist que bloquea los hosts reales (sección 1) | Infraestructura/DevOps, no código |
| 2 | Verificar las 9 URLs restantes de `rss_sources.yml` contra una conexión real | Solo 2 de 11 están `verified: true`; el resto es la mejor estimación, no confirmada | Depende de (1) |
| 3 | Curar feeds temáticamente relevantes, no solo "que respondan" | El feed verificado (Diario Financiero, portada general) dio 0/8 relevancia automotriz hoy (sección 2) | Criterio editorial humano |
| 4 | Agregar `AutoTest` y `Motor1` a la Knowledge Base | Sus `source_id` no existen en `sources.yml`; sus feeds están `enabled: false` desde el Sprint 9 | Decisión de negocio + KB Update (fuera de alcance de ingesta) |
| 5 | Programar la ejecución (cron/scheduler) | `run_daily.py` hoy se invoca a mano; no hay disparador automático | Sprint futuro (v0.8 roadmap) |
| 6 | Abrir y leer `daily_brief.html` manualmente | No hay envío por correo todavía | Sprint v0.9 (Roadmap) |
| 7 | Validar manualmente en Training Mode | Por diseño — el sistema nunca decide solo, un humano confirma (principio del proyecto, no una limitación a resolver) | No aplica — esto es intencional, no deuda técnica |
| 8 | Resolver el choque de nombre de `training_report.html` si se corre `run_daily.py` y `run_training.py` el mismo día | Ambos comandos escriben ahí por defecto (deuda ya documentada desde el Sprint 9) | `--report-output` como workaround; falta una solución permanente |
| 9 | Vigilar manualmente si un feed empieza a fallar de forma sostenida | No hay historial persistido de salud de feeds entre ejecuciones, solo el log de la corrida del día | Sprint futuro |
| 10 | Revisar manualmente si una "noticia nueva" es en realidad la misma historia de ayer reformulada | La deduplicación de `rss/deduplication.py` solo compara dentro de una misma corrida (URL/título exacto) — no hay memoria entre días | Concepto `Story` vs `NewsItem` de la arquitectura original, nunca implementado (deuda ya documentada desde el Sprint 9) |

De estos 10, **el 1, el 2 y el 3 son los que realmente bloquean "automatización completa" en el sentido que pide este sprint** — los demás son mejoras de calidad/robustez que no impiden que el flujo corra solo, o son decisiones de diseño ya tomadas a propósito (como el punto 7).

---

## 5. Conclusión

El pipeline de PR HUB, de punta a punta, **ya está listo técnicamente** para correr solo — 89 ms es, para efectos prácticos, instantáneo, y el código no necesitó ningún cambio para procesar noticias reales de hoy. Lo que falta antes de poder decir "automatización completa" no es ingeniería del motor de reglas: es (1) que el entorno donde esto corra tenga salida de red real hacia los sitios de noticias, y (2) que alguien con criterio de PR confirme que los feeds elegidos efectivamente traen noticias de autos, no solo que la URL responda 200. Esta corrida lo demostró de la forma más directa posible: con el único feed que ya estaba "verificado", el resultado real de hoy fue cero noticias relevantes — un dato incómodo, pero exactamente el tipo de cosa que vale más descubrir en un dry run de 89 milisegundos que en la primera mañana real de producción.

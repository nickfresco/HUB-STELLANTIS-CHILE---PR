# Media & Source Intelligence — Especificación de Arquitectura

**Sprint 9.6 · Stellantis PR Intelligence Hub**
**Estado: diseño. Nada de lo descrito aquí está implementado todavía.**

> Nota de alcance, antes de empezar: este documento diseña un módulo nuevo.
> No modifica `rule_engine/`, `classification/`, el Rulebook, la Knowledge
> Base existente (`config/knowledge_base/`), ni ninguna interfaz. No
> contiene código. Todo lo que sigue es arquitectura de producto, para
> decidir *qué construir* antes de construirlo — igual que las Partes 1-5
> del proyecto lo fueron para el Decision Engine.

> Nota sobre el documento de periodistas y medios mencionado: no venía
> adjunto a este mensaje — solo tengo los nombres que diste en el texto
> (Leonardo Pacheco, Ángeles Gana, Lorena Gallardo, Leonardo Mellado;
> Agenda Motor, AutoNoticias, The Clinic Auto Test, Press Latam, Al
> Volante). Los uso como semilla en la sección 12, pero **no invento**
> especialidad, cobertura ni confiabilidad sobre ellos — esos campos
> quedan explícitamente pendientes hasta que el documento real esté
> disponible. Inventar esos datos sería exactamente el tipo de decisión
> no auditable que este módulo existe para evitar.

---

## 1. Objetivos del módulo

Media & Source Intelligence (en adelante, **MSI**) es el componente
responsable de decidir, con evidencia y de forma auditable, **qué fuentes
vale la pena escuchar** — antes de que su contenido llegue al Decision
Engine.

Objetivos concretos:

1. **Reducir ruido.** El caso que originó este sprint (Sprint 9.5: 8/8
   noticias de Diario Financiero sin relevancia automotriz, todas cayendo
   igual en la sección Industria del Daily Brief) no debe repetirse sin que
   el sistema lo detecte y lo refleje.
2. **Aumentar relevancia.** Priorizar, con el tiempo, las fuentes que
   efectivamente producen contenido accionable para PR — no solo las que
   están técnicamente disponibles vía RSS.
3. **Aprender de forma continua y explicable.** El valor de una fuente no
   se decide una vez — se observa, se acumula evidencia, y se ajusta.
4. **Nunca depender exclusivamente de IA.** El aprendizaje es
   determinístico, basado en métricas medibles y reglas configurables —
   el mismo principio que ya gobierna el Rule Engine, aplicado ahora a
   fuentes en vez de a noticias individuales.
5. **Mantener al Coordinador de PR con la última palabra.** Cualquier
   fuente puede validarse, corregirse o forzarse manualmente, y esa
   decisión humana prevalece sobre el cálculo automático hasta que alguien
   la cambie explícitamente.

## 2. Filosofía

MSI hereda, deliberadamente, los mismos cuatro principios que ya gobiernan
el resto de PR HUB — no porque sea cómodo reutilizarlos, sino porque son
exactamente los principios correctos para este problema también:

- **Configuración y evidencia sobre intuición.** El score de una fuente es
  el resultado de reglas aplicadas a métricas observadas, no un juicio
  editorial del sistema ni una puntuación de un modelo de IA de caja
  negra.
- **Trazabilidad total.** Todo cambio de score o de tier debe poder
  explicarse: qué regla se aplicó, sobre qué evidencia, cuándo. El mismo
  patrón que ya existe en el Rule Engine (`matchedPriorityRules`) se
  extiende aquí como un registro equivalente por fuente.
- **Asistir, no decidir.** MSI puntúa y clasifica fuentes; no descarta
  contenido de forma silenciosa ni irreversible. Toda decisión de excluir
  algo queda visible y es reversible por un humano.
- **Aprendizaje lento y estable, no reactivo.** Un solo día malo (como el
  de Diario Financiero) no debe hundir una fuente. El sistema exige
  evidencia acumulada antes de actuar — esto se detalla en la sección 7.

## 3. Relación con lo que ya existe (para no duplicar)

Antes del modelo de datos, una aclaración necesaria: PR HUB ya tiene un
concepto de "fuente" — `Source` en `config/knowledge_base/sources.yml`,
con su propio `tier` (Tier 1/2/3, Especializado, Oficial, Corporativo,
Agencia). MSI **no reemplaza eso**. Lo complementa, y hay que ser precisos
sobre la diferencia:

| | `Source.tier` (ya existe) | MSI Tier (este diseño) |
|---|---|---|
| Qué mide | Prestigio/credibilidad editorial general del medio | Qué tan valiosa es esa fuente **específicamente para inteligencia de PR de Stellantis** |
| Cómo se asigna | Manual, una vez, al dar de alta la fuente | Aprendido, continuo, con evidencia acumulada |
| Ejemplo del caso Diario Financiero | Tier 1 (medio de negocios legítimo y confiable) — **esto no cambia** | Debería converger hacia Observación o Descartada para el feed general usado — **esto es lo nuevo** |

Esta distinción es el corazón de por qué el caso Diario Financiero no es
una contradicción: un medio puede ser editorialmente serio y, al mismo
tiempo, una mala fuente de señal automotriz — son dos preguntas distintas,
y hoy el sistema solo sabía responder la primera.

## 4. Modelo de datos

### 4.1 Dos niveles, no uno

El caso Diario Financiero revela algo que una ficha "por medio" no puede
capturar bien: es muy probable que Diario Financiero tenga una sección de
autos decente y una portada general irrelevante para este caso de uso —
pero el feed que se usó fue el de portada completa. Si MSI puntuara solo a
nivel de "Diario Financiero" como entidad única, terminaría penalizando al
medio completo por culpa de haber elegido el feed equivocado.

Por eso el modelo tiene **dos niveles**:

- **Fuente** — la entidad identitaria: un medio, un periodista, un canal,
  una agencia. Es donde vive la reputación general y la relación con otras
  fuentes (ej. "Leonardo Pacheco escribe para Agenda Motor").
- **Canal de Captura** — el punto de ingesta específico y medible: una URL
  de RSS puntual, una sección/tag, un canal de YouTube, una cuenta. **El
  score y el tier se calculan a nivel de Canal de Captura, no de Fuente.**
  Una Fuente puede tener varios Canales de Captura con desempeño muy
  distinto entre sí (la portada general de Diario Financiero vs. una
  eventual sección de autos serían dos Canales de Captura de la misma
  Fuente, con scores independientes).

Esto también resuelve, de paso, cómo modelar a un periodista freelance: es
una Fuente (tipo Persona) que puede estar asociada a uno o más Canales de
Captura (su columna en un medio, su cuenta de X, su propio newsletter),
cada uno puntuado por separado.

### 4.2 Ficha de Fuente

| Campo | Tipo | Quién lo determina |
|---|---|---|
| Nombre | Texto | Alta manual o descubrimiento automático |
| Tipo de Fuente | Catálogo cerrado (ver 4.4) | Alta manual |
| País | Texto | Alta manual |
| Especialidad declarada | Texto libre / catálogo de temas | Alta manual (puede refinarse con evidencia) |
| Relación con otras Fuentes | Lista de referencias (ej. "publica en") | Alta manual, editable |
| Estado | Catálogo (ver sección 6) | Calculado, con posible override manual |
| Última revisión | Fecha | Automático (cada vez que el estado se recalcula) o manual (cuando un humano valida) |
| Origen del alta | "Manual" / "Descubrimiento automático" / "Documento semilla" | Automático al crear la ficha |

### 4.3 Ficha de Canal de Captura (donde vive el scoring)

Esta es la ficha "permanente" que pedías, con los campos que listaste:

| Campo | Tipo | Cómo se determina |
|---|---|---|
| Fuente asociada | Referencia a Fuente | Alta manual |
| Nombre del canal | Texto (ej. "Diario Financiero — Portada RSS") | Alta manual |
| Tipo de canal | RSS / Sección con RSS / Newsletter / Canal de YouTube / Podcast / Cuenta social / Sitio sin feed | Alta manual |
| RSS disponible | Sí/No + URL si aplica | Alta manual, verificable (ver Sprint 9, `verified: true/false`) |
| Frecuencia de publicación | Numérica (items/semana, observada) | Calculada de evidencia histórica |
| Confiabilidad | Nivel (Alta/Media/Baja) | Calculada: ¿el contenido se corrige o retracta seguido? ¿coincide con el Tier editorial de `sources.yml` como señal inicial? |
| Velocidad | Nivel | Calculada: ¿gana o pierde el desempate de `primarySource` en Deduplication frente a otras fuentes de la misma historia? |
| Cobertura Stellantis | % | Calculada: de todo lo publicado por este canal, ¿qué % terminó con `brands` no vacío en el Decision Engine? |
| Cobertura Competencia | % | Igual, con `competitors` |
| Cobertura Industria | % | Igual, con Category=Industria |
| Cobertura Regulación | % | Igual, con EventType=RegulacionOPoliticaPublica |
| Cobertura Tecnología | % | Igual, con Category=Tecnología |
| Cobertura Motorsport | % | Igual, con Category=Motorsport |
| Cobertura Electrificación | % | Igual, con Category=Electrificación |
| Ruido | % | Calculada: % de contenido que termina "Sin clasificar" (sin brand, sin competitor, sin organization, sin event_type) — **esta es la métrica que habría marcado a Diario Financiero desde el primer día** |
| Duplicación | % | Calculada: % de contenido de este canal que la Deduplication descarta por ya existir de otra fuente que publicó primero |
| Valor PR | Nivel, parcialmente calculado + ajustable a mano | Calculada: % de contenido que termina en una `RecommendationAction` distinta de `SinAccionInmediata`; ajustable por el Coordinador cuando el juicio de negocio no coincide con la métrica cruda |
| Score final | Número (ver sección 5) | Calculado |
| Tier de Inteligencia | Catálogo (ver sección 6) | Calculado, con override manual posible |
| Última revisión | Fecha | Automática |
| Estado operativo | Activo / Pausado / Descartado | Calculado + override manual |

### 4.4 Catálogo de Tipo de Fuente

Medio especializado · Medio generalista · Sección de motores (dentro de un
medio generalista) · Organismo oficial · Blog · Sitio corporativo ·
Agencia internacional · Newsletter · Canal de YouTube · Podcast · Creador
de contenido · Periodista especializado (Persona).

Nota: "Persona" es un tipo de Fuente válido — esto es lo que permite
representar a un periodista freelance sin forzarlo dentro del modelo de
"medio", que es justo lo que este sprint pedía poder distinguir.

## 5. Sistema de scoring

El Score final no es una fórmula matemática cerrada — es una **agregación
ponderada de señales**, cada una con una dirección clara (sube/baja) y un
peso relativo. Se expresa aquí como reglas, no como ecuación, a propósito:
así queda tan auditable y editable como el Rulebook del Decision Engine.

| Señal | Efecto sobre el Score | Peso relativo | Justificación |
|---|---|---|---|
| Ruido alto y sostenido | Baja fuerte | Alto | Es la señal más directa de que el canal no aporta — caso Diario Financiero |
| Cobertura relevante alta (suma de las 7 categorías) | Sube | Alto | Es, literalmente, la razón de ser del canal |
| Duplicación alta (republica lo que otros ya publicaron) | Baja | Medio | No aporta primicia, aunque el contenido en sí no sea "ruido" temático |
| Velocidad alta (gana el desempate de `primarySource` seguido) | Sube | Medio | Señal de que suele publicar primero, no solo replicar |
| Valor PR alto (genera recomendaciones accionables, no solo clasificación) | Sube | Alto | Es el puente directo entre "el sistema clasificó esto" y "esto le sirvió al Coordinador" |
| Confiabilidad baja (contenido que se corrige/retracta) | Baja | Medio | Afecta la credibilidad de cualquier Daily Brief que la cite |
| Validación manual positiva del Coordinador (Training Mode) | Sube, con más peso que el cálculo automático | Muy alto | Es evidencia humana directa — pesa más que cualquier métrica derivada |
| Validación manual negativa del Coordinador | Baja, con más peso que el cálculo automático | Muy alto | Igual que arriba, en la dirección contraria |
| Evidencia insuficiente (canal nuevo) | No se calcula — el campo queda vacío, no en cero | — | Un score en cero por falta de datos es indistinguible de un score en cero por mal desempeño; hay que evitar esa confusión (ver sección 8) |

## 6. Sistema de tiers

**Tier de Inteligencia** (nuevo, a nivel de Canal de Captura — no confundir
con `Source.tier`, ver sección 3):

| Tier | Significado | Cómo se llega | Cómo se sale |
|---|---|---|---|
| **Tier 1 — Prioritaria** | Score alto sostenido, cobertura relevante consistente, baja duplicación, evidencia de velocidad o exclusividad | Score sobre el umbral alto durante toda la ventana de evidencia mínima (sección 7) | Cae a Tier 2 si el score baja del umbral durante una ventana completa (no un solo evento) |
| **Tier 2 — Confiable** | Cobertura relevante consistente, sin destacar en velocidad o exclusividad | Score sobre el umbral medio | Sube a Tier 1 con score sostenido alto; baja a Tier 3 con score sostenido bajo |
| **Tier 3 — Marginal** | Cobertura relevante ocasional, ruido moderado | Score sobre el umbral mínimo pero bajo | Sube con mejora sostenida; baja a Observación si el score sigue cayendo |
| **Experimental** | Canal nuevo, sin evidencia suficiente todavía | Estado inicial de todo canal nuevo, automático o dado de alta manualmente | Pasa a Tier 1/2/3 según el score, en cuanto se cumple la ventana de evidencia mínima — nunca antes |
| **Observación** | Score bajo o mixto; bajo revisión activa | Score por debajo del umbral mínimo, o comportamiento inconsistente (alta varianza) | Vuelve a Tier 3 si mejora; pasa a Descartada si el score sigue bajo tras la ventana de revisión |
| **Descartada** | Score consistentemente muy bajo o ruido sostenido cercano al 100% | Score bajo el umbral de descarte durante toda una ventana de revisión completa (nunca por un solo día) | Solo se reactiva manualmente — el sistema no vuelve a subir de tier una fuente Descartada por sí solo, para evitar oscilaciones |

Regla transversal, la más importante de toda esta sección: **ningún canal
cambia de tier por un solo día de evidencia.** El caso Diario Financiero
(1 corrida, 8/8 sin relevancia) es evidencia real pero insuficiente por sí
sola — ver sección 7 para el mecanismo exacto que evita actuar sobre eso
prematuramente.

## 7. Reglas de aprendizaje

Expresadas como el Rulebook del Decision Engine: condición → efecto,
siempre con `todo`/justificación cuando corresponde.

- **R1 — Ventana de evidencia mínima.** Ningún canal recibe un Score
  "real" (ni cambia de Tier) antes de acumular una ventana mínima de
  evidencia (ej. N publicaciones observadas o M días, lo que ocurra
  después). Antes de eso, el estado es `Experimental` y el Score queda
  explícitamente vacío, no en cero.
- **R2 — Ruido sostenido baja el score de forma marcada.** Si el % de
  Ruido se mantiene sobre un umbral alto durante toda la ventana de
  evidencia (no un solo día), el Score baja con el mayor peso de todas las
  señales.
- **R3 — Cobertura relevante sostenida sube el score.** Si la suma de
  cobertura relevante (las 7 categorías) se mantiene sobre un umbral
  durante la ventana, el Score sube.
- **R4 — Duplicación alta reduce el Valor PR, no necesariamente el Ruido.**
  Un canal que solo republica contenido ajeno no es "ruidoso" en el
  sentido temático (sí habla de autos), pero tampoco aporta — se penaliza
  aparte, no se mezcla con R2.
- **R5 — Velocidad sostenida (gana el desempate de fuente principal)
  sube el score.**
- **R6 — La validación manual del Coordinador en Training Mode pesa más
  que cualquier cálculo automático.** Si un humano marca contenido de un
  canal como correcto/incorrecto de forma repetida, esa señal ajusta el
  Score con más peso que las métricas derivadas — y puede anular
  directamente el Tier calculado (override).
- **R7 — Ninguna baja de Tier es automática hasta el final de una ventana
  de revisión completa**, ni siquiera con Score bajo — hay un período de
  "aviso" (el canal se marca para revisión, no se degrada de inmediato).
- **R8 — Ninguna fuente Descartada se reactiva sola.** Requiere acción
  humana explícita, registrada.
- **R9 — Todo cambio de Score o Tier se registra con la regla exacta que
  lo produjo y la evidencia asociada** (el equivalente, para MSI, de
  `matchedPriorityRules` en el Decision Engine) — sin esto, "auditable" es
  solo una palabra.

## 8. Casos borde

- **Medio generalista con una sección de autos buena.** Resuelto por el
  modelo de dos niveles (sección 4.1) — el canal de la sección de autos se
  puntúa aparte del canal de portada general.
- **Periodista freelance publicando en varios lugares.** Resuelto por
  "Persona" como Tipo de Fuente válido, con múltiples Canales de Captura
  asociados.
- **Canal nuevo, cero evidencia.** Score explícitamente vacío (no cero),
  Estado=Experimental — evita confundir "no sabemos" con "sabemos que es
  malo" (R1).
- **Fuente que se degrada con el tiempo** (cambio editorial, cambio de
  dueño). El Score se calcula sobre una ventana móvil, no acumulada desde
  el origen — una fuente que empeora ve su Score bajar en semanas, no
  nunca, aunque haya sido excelente por años.
- **Fuente valiosa sin RSS** (un periodista que solo publica en redes o un
  newsletter sin feed). Se registra la ficha igual (`RSS disponible: No`)
  — MSI puntúa y prioriza; conectar técnicamente esa fuente es trabajo de
  un futuro conector de ingesta, no de este módulo.
- **Contenido patrocinado o con conflicto de interés aparente** (ej. una
  nota pagada, ya identificado como deuda técnica en `validation_report.md`,
  ítem P8). Se marca como un atributo propio del contenido, no se confunde
  con "Ruido" — son dos problemas distintos.
- **El Coordinador no está de acuerdo con el Tier calculado.** El override
  manual (R6) prevalece y queda registrado como tal — el sistema no vuelve
  a "corregir" ese override automáticamente.
- **Una fuente nueva se descubre porque otra fuente confiable la cita
  repetidamente.** Se da de alta automáticamente, pero en Experimental —
  el descubrimiento automático nunca asigna un Tier alto de entrada (ver
  sección 9, riesgo de manipulación).

## 9. Riesgos

- **Sesgo de retroalimentación.** Si en el futuro el Tier llega a filtrar
  contenido antes del Decision Engine, una fuente de tier bajo deja de
  generar nueva evidencia (porque ya no se procesa su contenido) — su tier
  podría quedar congelado aunque mejore. Mitigación: mantener revisión
  periódica obligatoria de canales en Observación/Descartada, no solo
  cálculo pasivo.
- **Sobre-optimización hacia lo ya conocido.** El sistema podría converger
  a valorar solo fuentes Stellantis-céntricas y perder señal de industria
  amplia, que es valiosa aunque infrecuente — por eso "Cobertura Industria"
  es una señal propia (sección 4.3), no se descarta por tener menos volumen
  que "Cobertura Stellantis".
- **Ventanas mal calibradas.** Muy cortas, decisiones volátiles (exactamente
  lo que habría pasado si se hubiese actuado sobre el único día de Sprint
  9.5); muy largas, lentas para reaccionar a un cambio real.
- **Confundir "no hubo noticias de autos hoy" con "esta fuente es mala".**
  El Score se mide sobre tendencia en una ventana, nunca sobre un evento
  puntual — un día flojo de una fuente genuinamente automotriz no debería
  pesar igual que un día flojo de una fuente genuinamente irrelevante.
- **Concentración excesiva en pocas fuentes Tier 1.** Reduce diversidad de
  cobertura y aumenta el riesgo de perder una noticia real que solo cubrió
  una fuente marginal ese día.
- **Manipulación.** Al tratarse de medios y periodistas reales, existe un
  riesgo (bajo, pero real) de que una fuente optimice su contenido sabiendo
  que está siendo evaluada. Mitigación parcial: los criterios de scoring no
  son públicos, y el descubrimiento automático nunca otorga Tier alto sin
  evidencia sostenida.
- **Costo de mantenimiento.** Cientos de fichas completas es trabajo de
  curación real. No todas las fuentes necesitan el mismo nivel de detalle
  — ver recomendación de fases en la sección 11.

## 10. Cómo interactúa con el resto del sistema

| Componente | Relación con MSI |
|---|---|
| **RSS Collector** (`rss/`) | Hoy, `config/rss_sources.yml` decide qué feeds se consultan, de forma plana. A futuro, el Source Registry sería quien informa/sugiere ese archivo — no lo reemplaza de raíz sin revisión humana, y esta fase no toca `rss/` en absoluto. |
| **Decision Engine** (`rule_engine/`, `classification/`) | No cambia su lógica interna. En una fase futura (5+), podría recibir el Tier de la fuente como un campo más disponible en el `Fact` — usarlo o no en una regla sería una decisión de negocio posterior, no asumida por este diseño. |
| **Knowledge Base** (`config/knowledge_base/`) | MSI es una extensión conceptual de `sources.yml`, no un reemplazo. La Fase 1 (sección 11) no modifica ese archivo. |
| **Daily Brief** | A futuro, podría mostrar el Tier de la fuente junto a cada noticia, y (fase 5) beneficiarse de menos ruido tipo Diario Financiero llegando a la sección Industria. |
| **Weekly Report** | No existe todavía como módulo — es el concepto del clipping semanal original del proyecto, nunca construido como producto separado. MSI sería un insumo natural (ranking de fuentes de la semana) cuando se construya — se documenta como dependencia futura, no como trabajo de este sprint. |
| **Benchmark** | Tampoco existe todavía como módulo propio. Mismo tratamiento: dependencia futura documentada, no construida aquí. |
| **Source Registry** | Es el módulo en sí — el punto único de verdad sobre "qué sabemos de esta fuente", consultado por cualquier otro componente que lo necesite. |

## 11. Roadmap de implementación

- **Fase 1 — Modelo y semilla.** Crear el modelo de datos (Fuente + Canal
  de Captura) y poblar el Source Registry con las fuentes ya conocidas —
  incluyendo la semilla de la sección 12 — todas en Experimental u
  Observación. Sin scoring automático todavía; fichas editables a mano.
- **Fase 2 — Ruido, primero.** Implementar solo la métrica de Ruido,
  derivada de datos que el Decision Engine ya genera hoy (proporción de
  contenido "Sin clasificar" por canal). Es la señal más barata de todas —
  no requiere datos nuevos — y es exactamente la que habría anticipado el
  caso Diario Financiero. Incluye reprocesar retroactivamente lo ya
  generado en los Sprints 9 y 9.5 como primera evidencia real.
- **Fase 3 — Resto de señales + Score + Tiers.** Cobertura por categoría,
  Duplicación (vía el ganador de `primarySource`), Velocidad, Score final,
  y el sistema de Tiers — todo en modo solo-observación: se calcula y se
  muestra, no filtra nada todavía.
- **Fase 4 — Conexión con Training Mode.** Cada validación Sí/No ya es,
  implícitamente, una señal sobre la fuente de esa noticia, no solo sobre
  la noticia — conectar ese dato al Score (regla R6) es la primera fuente
  de evidencia humana explícita.
- **Fase 5 — Pre-filtro opcional y reversible.** Recién aquí MSI empieza a
  influir en qué llega al Decision Engine — y solo de forma auditable y
  revertible, nunca como descarte silencioso.
- **Fase 6 — Integración con Weekly Report / Benchmark.** Condicionada a
  que esos módulos se diseñen y construyan — no se puede planear en
  detalle algo que todavía no existe.

## 12. Semilla inicial del Source Registry

Los nombres que diste, cargados como Fuentes en estado **Experimental**
—no en un Tier alto de entrada, siguiendo la regla de la sección 8 sobre
descubrimiento— con los campos que sí puedo completar sin inventar nada:

| Nombre | Tipo de Fuente | Especialidad / Cobertura / Confiabilidad |
|---|---|---|
| Leonardo Pacheco | Persona (periodista especializado) | Pendiente — requiere el documento fuente |
| Ángeles Gana | Persona (periodista especializado) | Pendiente — requiere el documento fuente |
| Lorena Gallardo | Persona (periodista especializado) | Pendiente — requiere el documento fuente |
| Leonardo Mellado | Persona (periodista especializado) | Pendiente — requiere el documento fuente |
| Agenda Motor | Medio especializado (a confirmar) | Pendiente — requiere el documento fuente |
| AutoNoticias | Medio especializado | **Ya existe parcialmente**: `source.autonoticias` en `config/knowledge_base/sources.yml` (Sprint 5) — la ficha de MSI debería enlazar a esa entidad, no duplicarla |
| The Clinic Auto Test | Medio generalista con sección de autos (a confirmar) | Pendiente — requiere el documento fuente |
| Press Latam | Agencia o medio especializado (a confirmar) | Pendiente — requiere el documento fuente |
| Al Volante | Medio especializado (a confirmar) | Pendiente — requiere el documento fuente |

**Para cerrar esta tabla de verdad, hace falta el documento original** —
sube el PDF y completo Especialidad, Tipo exacto, y cualquier Canal de
Captura (RSS, redes, newsletter) que el documento indique, sin adivinar
nada de lo que no esté ahí.

---

## Respuestas directas a las preguntas del sprint

Para que quede explícito dónde vive cada respuesta en este diseño:

| Pregunta | Dónde se responde |
|---|---|
| ¿Qué fuentes generan mayor valor para Stellantis? | Score final + campo "Valor PR" (4.3, 5) |
| ¿Qué % del contenido de una fuente termina siendo útil? | Suma de campos "Cobertura [categoría]" (4.3) |
| ¿Qué fuentes generan demasiado ruido? | Campo "Ruido" (4.3) — la métrica que habría detectado el caso Diario Financiero |
| ¿Qué periodistas suelen publicar primicias? | Campo "Velocidad", vía el desempate de `primarySource` (4.3, 5) |
| ¿Qué medios suelen replicar información de otros? | Campo "Duplicación" (4.3) |
| ¿Qué fuentes publican información exclusiva? | Combinación de Velocidad alta + Duplicación baja |
| ¿Qué fuentes generan cobertura internacional? | Campo País (4.2) + análisis de Cobertura por categoría |
| ¿Qué fuentes cubren lanzamientos / regulación / electrificación / competencia? | Campos "Cobertura [categoría]" específicos (4.3), uno por cada dimensión |
| ¿Qué fuentes publican contenido lifestyle? | Especialidad declarada (4.2) + Tipo de Fuente (4.4) — requiere, a futuro, una categoría de Taxonomy propia si no existe ya |

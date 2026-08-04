# Validation Report — Ronda 1

**Fuente:** `training/validations/round_1.json` (16 noticias reales, julio/agosto 2026)
**Fecha de análisis:** basado en la primera ronda de validación manual del Coordinador de PR
**Alcance:** solo análisis. Ningún cambio de este documento fue implementado — eso es explícitamente el objetivo del Sprint Backlog al final.

---

## 1. Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Noticias totales validadas | 16 |
| Aciertos (`correct: true`) | 10 |
| Errores (`correct: false`) | 6 |
| **Precisión general** | **62,5%** |

De las 6 noticias marcadas como incorrectas, **2 comparten exactamente la misma causa raíz** (PR-013 no distingue marca propia de competencia), lo que significa que un solo cambio de regla podría mover la precisión medida en esta muestra de 62,5% a 75% sin tocar nada más. Eso se detalla en la sección 4.

Una advertencia sobre el tamaño de la muestra: 16 noticias es un n pequeño. Los porcentajes de esta sección son descriptivos de esta ronda, no una medición estadísticamente robusta del sistema — sirven para priorizar, no para certificar una tasa de acierto del producto.

---

## 2. Análisis por regla

| Regla | Activaciones | Correctas | Incorrectas | Precisión | Diagnóstico |
|---|---|---|---|---|---|
| **PR-001** (Recall Stellantis + Chile) | 2 | 2 | 0 | 100% | Funcionó correctamente en ambos casos reales (alertas SERNAC #0 y #1), incluyendo un caso de 6 marcas simultáneas. Sin cambios recomendados. |
| **PR-010** (Lanzamiento competidor) | 3 | 3 | 0 | 100% | Funcionó correctamente en los 3 casos (BYD, BAIC, Nissan). Sin cambios recomendados. |
| **PR-011** (Resultados ANAC) | 2 | 1 | 1 | 50% | Acertó en un reporte agregado sin marca propia destacada (#15, marcas chinas). Falló cuando el reporte destacaba positivamente a una marca Stellantis (#12, Peugeot líder en comerciales) — la regla no distingue ese caso del genérico. |
| **PR-012** (Regulación) | 1 | 0 | 1 | 0% | Única activación marcada como incorrecta (#13), pero sin campos de corrección completados por el Coordinador — ver nota en sección 3, categoría F. No hay evidencia suficiente para concluir que la lógica de la regla esté mal; es más probable un problema de visibilidad de datos en el reporte que un error de clasificación. |
| **PR-013** (Latin NCAP) | 2 | 0 | 2 | 0% | Falló en ambas activaciones (#11 Toyota, #14 protocolo Latin NCAP). Causa raíz única y ya señalada en revisiones de arquitectura anteriores (Parte 2B): la regla nunca se acotó a marcas Stellantis, así que trata igual un resultado de seguridad de una marca propia que de un competidor. Es el hallazgo de mayor impacto de esta ronda — ver sección 4. |
| PR-002, PR-004, PR-008 | 0 | — | — | — | Ninguna de las 16 noticias activó estas reglas. No es evidencia de que fallen ni de que funcionen — es una brecha de cobertura del set de entrenamiento, no de las reglas. Recomendación: la próxima ronda de `training/examples/` debería incluir al menos una noticia real que las ejercite (ej. un lanzamiento o premio de marca Stellantis, no solo de competencia). |

---

## 3. Análisis por tipo de error

### Entity Recognition
- **#4** — El Coordinador espera que la marca detectada sea `"Stellantis"`, pero `brands.yml` no tiene una entidad corporativa "Stellantis"; solo sus 8 sub-marcas (Peugeot, Citroën, Opel, DS, Fiat, Jeep, RAM, Leapmotor). La noticia menciona al grupo directamente, sin nombrar ninguna sub-marca, así que Entity Recognition no tenía nada que detectar. Esto no es un bug de código — es exactamente la ambigüedad de "Marca Stellantis" señalada desde la revisión del Rulebook v0.1 (Riesgo B), ahora confirmada con un caso real.

### Priority
- **#11 y #14** — PR-013 asigna `HIGH` tanto si el resultado de Latin NCAP afecta a una marca Stellantis como si afecta a un competidor (Toyota). El Coordinador corrige ambos a `Low`.
- **#12** — PR-011 asigna `MEDIUM` de forma uniforme a cualquier reporte ANAC, sin distinguir cuando el reporte destaca positivamente a una marca propia (Peugeot liderando comerciales). El Coordinador corrige a `High`.

### Recommendation
- **#11** — `EvaluarQyA` no tiene sentido cuando el hecho no involucra a Stellantis: preparar Q&A es una acción defensiva propia, no aplica a un resultado de un competidor. El Coordinador corrige a `Monitorear` (mismo espíritu que `MonitorearEvolucion`, ya en el catálogo).
- **#12** — Falta `EvaluarComunicado` como recomendación cuando una marca propia lidera positivamente un segmento — hoy la regla no emite ninguna recomendación proactiva en ese escenario.
- **#4** — El Coordinador propone `"Clippear nota"`, que no es un valor del catálogo `RecommendationAction` actual (9 valores cerrados, Parte 2B sección 5.6). Puede ser una brecha real de catálogo, o simplemente vocabulario distinto para algo que ya cubre `SinAccionInmediata` — requiere aclarar con el Coordinador antes de tocar el catálogo.

### Rulebook incompleto
- **#4** — Ninguna regla activa cubre `AlianzaOAcuerdoComercial` para una marca Stellantis. La noticia queda sin prioridad ni recomendación, cuando el Coordinador espera `Low` + una acción de registro.
- **#7** — Ninguna regla activa cubre contenido operativo/logístico de un competidor (el buque de BYD). Además, Event Detection no pudo inferir ningún `EventType` para este texto (palabras como "buque", "flota", "transportar" no están en el diccionario de keywords) — así que ni siquiera había un `EventType` sobre el cual una regla pudiera evaluar. El Coordinador espera `Low` + `Monitorear`.

### Knowledge Base incompleta
- **#4** — Ya cubierto arriba (falta entidad "Stellantis" corporativa). Se repite aquí porque es simultáneamente un problema de Knowledge Base y de Rulebook: aunque se agregara la regla de AlianzaOAcuerdoComercial, no serviría de nada si la entidad "Stellantis" sigue sin existir para que la condición de marca la detecte.

### Herramienta / Reporte de validación (categoría no listada en el pedido original, pero surgida de la evidencia)
- **#13 y #14** — En ambos casos, el Coordinador usó el campo "Marca correcta" para nombrar un **organismo** (`"Anac"`, `"Latin Ncap"`), no una marca. `training_report.html` (Sprint 5) solo muestra la fila "Marca detectada" con `brand`/`competitors` — nunca expone qué `Organization` fue detectada. Es probable que ANAC y Latin NCAP sí hayan sido detectados correctamente por Entity Recognition (de hecho, ambas reglas PR-012 y PR-013 requieren esas organizaciones en su condición, y sí dispararon), pero el Coordinador no tenía forma de verlo en el reporte y usó el único campo de entidad disponible. Esto es un hallazgo importante: probablemente **no son errores del Rule Engine**, sino evidencia de que el reporte necesita mostrar más contexto antes de la próxima ronda — de lo contrario, futuras rondas de validación van a seguir generando este mismo ruido.

---

## 4. Propuestas de mejora

Cada propuesta indica el archivo a modificar, el cambio recomendado y el impacto esperado. **Ninguna fue implementada** — quedan documentadas para decidir en el Sprint Backlog.

### P1 — Agregar entidad corporativa "Stellantis" a la Knowledge Base
- **Archivo:** `config/knowledge_base/brands.yml`
- **Cambio:** agregar una entidad `brand.stellantis` (displayName "Stellantis"), separada de las 8 sub-marcas existentes, con sus alias razonables (ej. "Grupo Stellantis").
- **Impacto esperado:** resuelve directamente el error de Entity Recognition de #4, y probablemente destrabe otras noticias corporativas futuras (resultados financieros globales, alianzas, nombramientos) que mencionan al grupo sin nombrar una sub-marca — un patrón que ya apareció en al menos 2 de las 16 noticias de esta ronda (#3 y #4 mencionan "Stellantis" directamente).

### P2 — Regla para contenido de alianza comercial de marca Stellantis
- **Archivo:** `config/rules/priority_rules.yml`, `config/rules/recommendation_rules.yml`
- **Cambio:** nueva regla (o ampliación de PR-002) que cubra `event_type: AlianzaOAcuerdoComercial` cuando hay marca Stellantis presente → `Low` + una recomendación de registro/monitoreo.
- **Impacto esperado:** resuelve la mitad del error de #4 (la otra mitad depende de P1). Depende de P1 para funcionar.

### P3 — Acotar PR-013 (Latin NCAP) para distinguir marca propia de competencia
- **Archivo:** `config/rules/priority_rules.yml`, `config/rules/recommendation_rules.yml`
- **Cambio:** dividir la regla en dos: `PR-013` (marca Stellantis + `ResultadoDeSeguridad`) mantiene `High` + `EvaluarQyA`; una regla nueva (competidor + `ResultadoDeSeguridad`) → `Low` + `MonitorearEvolucion`.
- **Impacto esperado:** el más alto de todas las propuestas — resuelve 2 de los 6 errores de esta ronda (33%) con un solo cambio bien delimitado, y cierra una ambigüedad que ya se había señalado en la revisión de la Parte 2B antes de escribir una sola regla en YAML.

### P4 — Regla de monitoreo genérico para movimientos operativos/logísticos de competencia
- **Archivo:** `config/knowledge_base/event_types.yml` (posible nuevo valor, ej. `CadenaDeSuministro`), `classification/event_detection.py` (nuevas keywords), `config/rules/priority_rules.yml`, `config/rules/recommendation_rules.yml`
- **Cambio:** agregar un `EventType` que cubra anuncios logísticos/operativos (envíos, flotas, plantas), o remapear a uno existente si se prefiere no ampliar el catálogo; luego una regla competidor + ese `EventType` → `Low` + `MonitorearEvolucion`.
- **Impacto esperado:** resuelve el error de #7 y previene que futuras noticias logísticas de competencia queden sin clasificar — es un patrón de noticia común (llegadas de buques, apertura de plantas) que probablemente se repita.

### P5 — PR-011: escalar cuando el resultado agregado destaca positivamente a una marca propia
- **Archivo:** `config/rules/priority_rules.yml`, `config/rules/recommendation_rules.yml`
- **Cambio:** condición adicional sobre PR-011 para el caso "marca Stellantis mencionada favorablemente" → `High` + `EvaluarComunicado`, distinto del caso genérico que se mantiene en `Medium` + `SinAccionInmediata`.
- **Impacto esperado:** resuelve el error de #12. **Advertencia de dependencia:** distinguir "favorable" de "desfavorable" requiere una señal de tono/sentimiento que hoy no existe en el modelo (el mismo vacío que ya mantiene a PR-003 en estado PENDING desde el Sprint de Decision Rules). Esta propuesta probablemente no se pueda implementar de forma aislada — es evidencia adicional a favor de priorizar esa deuda técnica, no un ajuste de una sola línea.

### P6 — Mostrar la Organization detectada en `training_report.html`
- **Archivo:** `training/report_renderer.py`
- **Cambio:** agregar una fila "Organismo detectado" en cada tarjeta, igual que ya existe "Marca detectada".
- **Impacto esperado:** no corrige ninguna regla, pero mejora la calidad de **todas** las rondas de validación futuras. Es probable que hubiera evitado la ambigüedad de #13 y #14 en esta misma ronda. Costo de implementación bajo, beneficio compuesto (afecta cada ronda futura, no solo un caso puntual).

### P7 — Revisar vocabulario del catálogo `RecommendationAction` con el Coordinador
- **Archivo:** ninguno todavía — requiere conversación, no cambio directo. Eventualmente `config/rules/recommendation_rules.yml` y la Parte 2B (modelo de dominio) si se decide ampliar el catálogo.
- **Cambio:** aclarar si `"Clippear nota"` (comentario de #4) corresponde a un valor ya existente con otro nombre, o si falta un valor nuevo tipo "Archivar/Registrar sin acción".
- **Impacto esperado:** bajo por sí solo (una sola mención en 16 noticias), pero evita ambigüedad si el patrón se repite en próximas rondas.

### P8 — (Fuera de alcance inmediato) Modelar contenido pagado vs. editorial
- **Archivo:** sin definir — requeriría diseño adicional al modelo de dominio (Parte 2B), no es un ajuste de configuración.
- **Cambio:** el comentario de #4 ("es una nota pagada por Stellantis y Santander") señala que el sistema no distingue cobertura editorial de contenido patrocinado — una dimensión que hoy no existe en ningún catálogo.
- **Impacto esperado:** potencialmente alto (afecta cómo se interpreta cualquier alianza comercial cubierta en medios), pero es la propuesta menos definida de todas — se deja registrada como hallazgo, no como tarea ejecutable todavía.

---

## 5. Sprint Backlog Priorizado

Ordenado por impacto esperado sobre la precisión medible y el costo de no resolverlo, no por orden de aparición en este documento.

| # | Propuesta | Resuelve | Impacto | Esfuerzo | Dependencias |
|---|---|---|---|---|---|
| 1 | **P3** — Acotar PR-013 (marca propia vs. competencia) | #11, #14 (2/6 errores) | **Alto** — mayor impacto cuantitativo de la ronda | Bajo — una regla existente se divide en dos | Ninguna |
| 2 | **P1** — Agregar entidad "Stellantis" a `brands.yml` | #4 (parcial) | Alto — desbloquea P2 y probablemente noticias corporativas futuras no vistas aún | Bajo — una entidad más en un archivo ya existente | Ninguna |
| 3 | **P2** — Regla para AlianzaOAcuerdoComercial de marca Stellantis | #4 (completa junto a P1) | Medio | Bajo | Depende de P1 |
| 4 | **P6** — Mostrar Organization en `training_report.html` | Mejora de proceso, no un error puntual | Medio — beneficio compuesto en cada ronda futura | Bajo | Ninguna |
| 5 | **P4** — Regla de monitoreo genérico competencia/logística | #7 | Medio | Medio — requiere tocar `event_types.yml` y `event_detection.py`, no solo reglas | Ninguna |
| 6 | **P5** — PR-011 escala con resultado positivo de marca propia | #12 | Medio | Alto — bloqueado por la ausencia de señal de tono/sentimiento | Deuda técnica de Sentiment Analysis (ver PR-003) |
| 7 | **P7** — Revisar vocabulario de `RecommendationAction` | Ambigüedad de #4 | Bajo | Bajo, pero requiere conversación primero | Ninguna |
| 8 | **P8** — Modelar contenido pagado vs. editorial | Hallazgo de #4, sin resolver | Desconocido — el más especulativo | Alto — requiere diseño, no solo configuración | Ninguna definida aún |

**Recomendación de foco para el próximo sprint:** los ítems 1 a 4 son todos de esfuerzo bajo y no dependen entre sí más que P2→P1 — se podrían implementar juntos en una sola pasada y, según esta muestra, elevarían la precisión medida de 62,5% a un rango estimado de 81-87% (resolviendo 3 a 4 de los 6 errores observados). Los ítems 5, 7 y 8 conviene dejarlos para una discusión de negocio aparte antes de tocar código, ya que ninguno es un cambio de una sola línea.

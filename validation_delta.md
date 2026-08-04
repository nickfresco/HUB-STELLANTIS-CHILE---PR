# Validation Delta — Ronda 1 vs. Sprint 7 (P1–P4)

**Compara:** `training/validations/round_1.json` (system output + validación manual del Coordinador) contra el mismo pipeline, sobre las mismas 16 noticias de `training/examples/`, después de implementar P1-P4.

**Nota de método, importante:** este documento **no** es una nueva ronda de validación manual — el Coordinador todavía no volvió a revisar nada. Es una comparación automática: se re-corrió el sistema sobre las 16 noticias de la Ronda 1 y se verificó si la nueva salida coincide con lo que el Coordinador ya había indicado como correcto en esa ronda. Es una estimación razonable de hacia dónde se movió la precisión, no una medición nueva — por eso el Sprint Backlog al final recomienda una Ronda 2 real antes de sacar conclusiones definitivas.

---

## Precisión

| | Precisión | Aciertos |
|---|---|---|
| **Antes** (Ronda 1, validación manual real) | 62,5% | 10/16 |
| **Después** (estimado, ver metodología) | **75,0%** | 12/16 |

---

## Qué noticias cambiaron de clasificación

De las 16, **3 cambiaron** de prioridad/regla activada; las otras 13 quedaron exactamente igual (verificado explícitamente — ver sección "Sin regresiones" más abajo).

| # | Noticia | Antes | Después |
|---|---|---|---|
| 4 | Crédito automotriz Stellantis + Santander Consumer | Sin clasificar | **LOW** (PR-016) |
| 11 | Toyota Yaris — Latin NCAP | **HIGH** (PR-013) | **LOW** (PR-017) |
| 14 | Latin NCAP endurece protocolo 2026 | **HIGH** (PR-013) | Sin clasificar |

---

## Qué noticias mejoraron

### #4 — Crédito automotriz Stellantis + Santander Consumer → **Resuelta (con una aproximación)**
- **Prioridad:** de sin clasificar a `Low` — coincide exactamente con la corrección del Coordinador.
- **Entidad:** ahora `Organismos detectados: Stellantis` — coincide con `brand_correct: "Stellantis"` de la Ronda 1 (P1 la modela como Organization, no Brand; ver nota de diseño en la sección de implementación del Sprint).
- **Recomendación:** el sistema asigna `SinAccionInmediata`. El Coordinador había escrito `"Clippear nota"`, que no existe en el catálogo `RecommendationAction`. Se usó la opción más fiel disponible — **no es una coincidencia exacta**, sigue abierto como ítem P7 del backlog (revisar vocabulario con el Coordinador).

### #11 — Toyota Yaris, Latin NCAP → **Resuelta**
- Prioridad `HIGH` incorrecta → `Low`, coincide con la corrección.
- Recomendación: `EvaluarQyA` (sin sentido para un competidor) → `MonitorearEvolucion` + `CompartirAnalisisCompetitivo`. Coincide con `"Monitorar"` de la corrección, y agrega la señal de inteligencia competitiva pedida explícitamente en el Sprint 7 (P3).
- Esta es, en la práctica, la corrección más limpia de las tres — el caso que motivó dividir la regla.

### #14 — Latin NCAP endurece protocolo 2026 → **Mejoró, no totalmente resuelta**
- Prioridad `HIGH` (incorrecta, con recomendación de Q&A que ni siquiera aplicaba) → sin clasificar.
- El propio comentario del Coordinador en la Ronda 1 decía *"el Q&A es solo si afecta directamente a Stellantis"* — el sistema ya no lo sugiere, así que dejó de estar activamente equivocado. Pero tampoco llegó a una clasificación positiva: esta noticia es sobre un cambio de protocolo a nivel de toda la industria, no sobre un modelo específico de una marca o competidor, así que ni PR-013 ni PR-017 (ninguna de las dos exige marca/competidor) tienen una condición que la cubra. Necesitaría una regla nueva para anuncios regulatorios/metodológicos de organismos de seguridad — **fuera del alcance de P1-P4**, quedó fuera de este sprint a propósito.

---

## Qué noticias siguen incorrectas

### #7 — Buque BYD Changzhou → **Sin cambios**
- Sigue sin clasificar. Su causa (sin `EventType` inferible + sin regla de monitoreo genérico para movimientos operativos/logísticos de competencia) corresponde al ítem **P4 del backlog original** (`validation_report.md`) — que **no es el mismo P4 de este sprint**. El P4 de Sprint 7 era mostrar entidades en el reporte; el P4 del backlog (regla de monitoreo genérico) sigue pendiente. Ver nota de nomenclatura al final.

### #12 — ANAC ventas, Peugeot lidera comerciales → **Sin cambios**
- Sigue en `Medium` + `SinAccionInmediata`; el Coordinador esperaba `High` + `EvaluarComunicado`. Corresponde al ítem **P5 del backlog** (escalar PR-011 cuando destaca positivamente a una marca propia), explícitamente bloqueado por la falta de una señal de tono/sentimiento — no estaba entre los aprobados para este sprint.

### #13 — ANAC permiso de circulación EV → **Sin cambios en la clasificación, pero la causa probable ya se corrigió**
- Prioridad y regla exactamente iguales (`Medium`, PR-012) — Sprint 7 no tocó PR-012.
- Sin embargo, `validation_report.md` (sección 3, categoría "Herramienta/Reporte") planteaba que este caso probablemente no era un error del Rule Engine, sino que el Coordinador no podía ver que `ANAC` sí había sido detectada, porque el reporte de la Ronda 1 no mostraba Organizations. Verificado: con el sistema actual, `Organismos detectados: ANAC` **sí aparece** para esta noticia. La clasificación no cambió porque no había ninguna regla que dependiera de eso — lo que cambió es que ahora el Coordinador puede confirmar si el `Medium` le parece correcto una vez que ve el dato completo. **No se cuenta como resuelta en la precisión estimada** (sería anticipar el juicio del Coordinador), pero es la candidata más probable a cambiar en una Ronda 2 real.

---

## Sin regresiones

Las 10 noticias que la Ronda 1 marcó como correctas (`#0, #1, #2, #3, #5, #6, #8, #9, #10, #15`) mantienen exactamente la misma prioridad y las mismas reglas activadas que antes — verificado programáticamente, no solo revisado a ojo. Ninguno de los cuatro cambios (P1-P4) rompió un caso que ya funcionaba.

---

## Efecto secundario observado (fuera del set de entrenamiento, para que no sea sorpresa)

`daily_brief.html` (datos ficticios de `data/daily_input/`, Sprint 4) también cambió al regenerarse: los Flash Alerts bajaron de 2 a 1. La causa es la misma lógica de P3: el fixture `02_latin_ncap_resultado_seguridad.json` menciona *"modelos de Stellantis"* de forma genérica, sin nombrar ninguna sub-marca — ahora se detecta `Stellantis` como Organization (P1), pero PR-013 exige `brands` (una sub-marca específica), así que ya no dispara. No se modificó ese fixture porque está fuera del alcance de P1-P4 (son datos ficticios de demostración, no evidencia real de validación) — queda anotado aquí para que el cambio de número en el Daily no sea una sorpresa si lo comparas con capturas anteriores.

---

## Nota de nomenclatura (para evitar confusión en el próximo sprint)

Este Sprint 7 definió su propio **P1-P4**, que **no coincide** con la numeración P1-P8 de `validation_report.md`:

| Sprint 7 | Corresponde a `validation_report.md` |
|---|---|
| P1 (entidad Stellantis) | P1 |
| P2 (regla de alianza comercial) | P2 |
| P3 (dividir PR-013) | P3 |
| P4 (mostrar entidades en el reporte) | **P6**, no P4 |

El **P4 real del backlog original** (regla de monitoreo genérico para movimientos de competencia — el que habría resuelto #7) y el **P5** (escalar PR-011) siguen pendientes, sin renombrar. Para el próximo sprint conviene referirse a ellos por descripción, no solo por número, para no repetir esta ambigüedad.

---

## Resumen de cambios implementados

- **P1** — `config/knowledge_base/organizations.yml`: nueva entidad `org.stellantis` (Organization, no Brand), con `organization_type: Manufacturer` (valor nuevo en ese catálogo). Verificado que no afecta la detección de ninguna de las 8 sub-marcas.
- **P2** — `config/rules/priority_rules.yml` + `recommendation_rules.yml`: nueva regla `PR-016` (`organizations` contiene `org.stellantis` + `event_type: AlianzaOAcuerdoComercial` → `Low` + `SinAccionInmediata`).
- **P3** — mismos dos archivos: `PR-013` ahora exige `brands` (marca Stellantis) además de Latin NCAP + `ResultadoDeSeguridad`; nueva regla `PR-017` cubre el caso de competencia (`competitors` en vez de `brands`) → `Low` + `MonitorearEvolucion` + `CompartirAnalisisCompetitivo`.
- **P4** — `training/report_renderer.py`: la fila combinada "Marca detectada" se reemplazó por tres filas independientes (Marcas Stellantis / Competidores / Organismos), y el JSON exportado ahora trae `system_brands`, `system_competitors` y `system_organizations` por separado en vez de un único `system_brand`.
- **Rule Engine:** sin cambios (tal como pedía el sprint — todo se resolvió con configuración y con el renderer de reporte).
- **Tests:** 65 → 74 (9 nuevos: 3 de P1, 2 de P2, 2 de P3, 5 de P4 — el conteo no cuadra 1 a 1 porque algunos tests cubren más de un punto). Los 74 pasan.
- **Commits:** 10 commits pequeños, uno por cambio de configuración y uno por su test correspondiente, sin squash.

---

## Backlog restante, priorizado

| # | Ítem (de `validation_report.md`) | Resuelve | Estado |
|---|---|---|---|
| 1 | P4 original — regla de monitoreo genérico para movimientos operativos/logísticos de competencia | #7 | Pendiente |
| 2 | P5 — escalar PR-011 con resultado positivo de marca propia | #12 | Pendiente, bloqueado por falta de señal de tono/sentimiento (mismo gap que PR-003) |
| 3 | P7 — revisar vocabulario de `RecommendationAction` con el Coordinador | Ambigüedad de #4 (`"Clippear nota"`) | Pendiente, requiere conversación antes que código |
| 4 | P8 — modelar contenido pagado vs. editorial | Hallazgo de #4, sin resolver | Pendiente, el más especulativo, sin diseño aún |
| — | **Nuevo, no estaba en la Ronda 1:** correr una Ronda 2 de validación manual real sobre estas mismas 16 noticias (o un set nuevo) para confirmar la precisión estimada de 75% y, en particular, resolver #13 con el Coordinador viendo ya el dato de Organization | #13 y confirmación general | Recomendado antes de tocar más reglas — es más barato validar que seguir adivinando sobre una muestra de 16 |

# Stellantis PR Intelligence Hub — MVP (Sprint 3 + Sprint 4 + Sprint 5)

Primer MVP funcional del Decision Engine: procesa una noticia y genera
un Daily Brief estructurado, siguiendo el Priority Rulebook v0.2 y las
Decision Matrices ya definidas — sin IA, completamente basado en
reglas.

**Sprint 4 (PR HUB Daily)** agrega la experiencia de usuario real:
`python run_daily.py` procesa las noticias del día y genera
`daily_brief.html`, un correo ejecutivo listo para abrir en el
navegador o pegar en Gmail/Outlook — sin tocar el Rule Engine, la
Knowledge Base ni ningún YAML existente.

**Sprint 5 (Modo de Entrenamiento)** agrega `run_training.py`: procesa
noticias **reales** (`training/examples/`, 16 noticias de julio/agosto
2026) y genera `training_report.html`, un reporte para validar a mano
si el criterio del Rule Engine coincide con el criterio real del
Coordinador de PR — sin aprendizaje automático, sin IA, sin nuevas
integraciones.

## Pipeline

```
Input JSON
  ↓
Entity Recognition     (classification/entity_recognition.py)
  ↓
Event Detection        (classification/event_detection.py)
  ↓
Priority Rule Engine    (rule_engine/ + config/rules/priority_rules.yml)
  ↓
Recommendation Engine   (rule_engine/ + config/rules/recommendation_rules.yml)
  ↓
Daily Brief Generator  (brief/generator.py)
  ↓
Output JSON
```

Cada etapa está desacoplada (`pipeline/stages.py`) y se puede
reemplazar de forma independiente — ver `tests/test_pipeline.py`, que
demuestra reemplazar Entity Recognition por una implementación falsa
sin tocar ninguna otra etapa.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py tests/fixtures/recall_jeep_chile.json
```

Devuelve el Daily Brief de esa noticia como JSON por stdout.

## Formato de entrada (`noticia.json`)

```json
{
  "title": "Texto del titular",
  "summary": "Resumen o cuerpo de la noticia",
  "source_id": "source.emol",
  "event_type": "Recall",
  "market_impact": ["Chile"],
  "tone": "positive"
}
```

- `title`, `summary`, `source_id`: obligatorios. `source_id` debe
  existir en `config/knowledge_base/sources.yml`.
- `event_type`: **opcional**. Si no se informa, se infiere de forma
  determinística por palabras clave (`classification/event_detection.py`).
  Si no viene y tampoco se puede inferir, queda en `null` y ninguna
  regla que dependa de `event_type` se activa (no es un error).
- `market_impact`, `tone`: opcionales, campos-placeholder de deuda
  técnica (ver sección siguiente).

## Correr los tests

```bash
pytest tests/ -v
```

42 tests del Sprint 3 + 14 tests de `daily/` (Sprint 4) + 9 tests de
Sprint 5 (7 de `training/report_renderer.py` + 2 de regresión del bug
de Entity Recognition) = **65 tests**, cubriendo: Knowledge Base
Loader, Entity Recognition (alias, desambiguación, y el fix de límites
de palabra), Event Detection, Rule Engine (AND/OR/NOT anidados,
`single_winner`, `accumulate_all`, reglas deshabilitadas), pipeline
desacoplado, el flujo end-to-end con noticias ficticias, la
agregación/etiquetado del Daily, y el reporte de validación manual del
modo de entrenamiento.

## Estado del Rulebook

De las 15 reglas del Priority Rulebook v0.2:

- **8 READY** (`enabled: true`): PR-001, PR-002, PR-004, PR-008,
  PR-010, PR-011, PR-012, PR-013.
- **7 PENDING** (`enabled: false`, con su dependencia declarada en el
  campo `todo` de cada regla en el YAML): PR-003, PR-005, PR-006,
  PR-007, PR-009, PR-014, PR-015.

Las reglas PENDING están registradas y se auditan como cualquier otra,
pero nunca se evalúan mientras estén deshabilitadas — no requieren
ningún concepto nuevo en el motor.

## PR HUB Daily (Sprint 4)

Genera el Daily Brief ejecutivo del día en HTML, a partir de todas las
noticias en `data/daily_input/`:

```bash
python run_daily.py
```

Esto:
1. Corre el pipeline existente (sin modificarlo) sobre cada archivo
   `.json` de `data/daily_input/`, en orden alfabético.
2. Agrupa los resultados (`daily/aggregator.py`) en Flash Alerts,
   Stellantis (por marca), Competencia (por marca), Industria y
   Oportunidades PR.
3. Renderiza `daily_brief.html` (`daily/html_renderer.py`) — diseño
   tipo correo ejecutivo, basado en tablas con estilos inline (pensado
   para verse bien tanto en navegador como pegado en Gmail/Outlook).

Opciones:
```bash
python run_daily.py --input otra_carpeta/ --output otro_nombre.html
```

Un archivo mal formado o con datos inválidos no detiene la ejecución
del resto del día — se reporta como error (consola + sección Debug del
HTML) y se continúa, conforme al principio de resiliencia ya definido
en la Parte 5.

### Cómo abrir el resultado

`daily_brief.html` ya viene generado en la raíz del repo con las 14
noticias de ejemplo de `data/daily_input/` — ábrelo directo en el
navegador para verlo sin correr nada. La sección **🧠 Debug** al final
(colapsable) muestra, por noticia, la marca detectada, el EventType
(y si fue explícito o inferido), la prioridad, las reglas activadas y
las Recommendation Actions — pensada para que revisemos juntos si el
sistema "pensó como un Coordinador de PR" antes de mostrárselo a
alguien más. Para ocultarla en una versión de producción, hay que
quitar la llamada a `_debug_section(...)` en
`daily/html_renderer.py:render_html` (queda como TODO, ver más abajo —
deliberadamente no se automatizó con un flag todavía).

### Qué es nuevo vs. Sprint 3 (sin tocar lo existente)

- `daily/labels.py` — traducción de `RecommendationAction` a frases
  legibles, y las plantillas de "por qué es un benchmark útil" /
  "por qué importa para Stellantis" (por `EventType`, texto fijo, sin IA).
- `daily/aggregator.py` — agrupa los briefs ya generados por el
  pipeline; no vuelve a evaluar ninguna regla.
- `daily/html_renderer.py` — el HTML en sí.
- `run_daily.py` — orquesta todo lo anterior.
- `data/daily_input/` — 14 noticias ficticias de ejemplo (Flash,
  Stellantis con las 8 marcas, Competencia, Industria, y una sin
  `event_type` explícito para probar la inferencia).
- Cambios aditivos (no rompen nada existente, 56/56 tests siguen
  pasando): `brief/generator.py` ahora también expone `competitors`,
  `organizations`, `source` y `why_it_matters` en el diccionario de
  salida (reutiliza `Rule.description`, ya escrito en
  `priority_rules.yml` — no genera texto nuevo); `RuleRegistry` ganó
  un método `get_rule(id)` de solo lectura para poder mostrar esa
  descripción.



Todo lo siguiente fue una decisión consciente para no bloquear el MVP,
no un olvido:

1. **`Story.market` no está resuelto formalmente.** `market_impact` es
   un campo de entrada explícito (proxy manual) hasta que se defina el
   mapeo real en el modelo de dominio (Riesgo B, revisión del Rulebook v0.1).
2. **Sentiment Analysis no existe.** El campo `tone` es un placeholder
   manual; las reglas que dependen de él (PR-003) quedan PENDING.
3. **Person nunca se implementó como catálogo** (no existe
   `persons.yml`) — hallazgo nuevo de este sprint. Bloquea PR-015.
4. **"Comparativa" y "Test Drive" no existen en `event_types.yml`** —
   bloquea PR-014 y limita PR-003.
5. **No hay deduplicación entre noticias** (no hay `Story` que agrupe
   varias `NewsItem`, no hay `StoryState`). Cada noticia se procesa de
   forma aislada. Es la simplificación más grande del MVP respecto a
   la Parte 2B.
6. **Taxonomy Engine real no implementado.** Event Detection es una
   heurística de palabras clave embebida en Python (`classification/event_detection.py`),
   no un motor de reglas configurable en YAML. Suficiente para el MVP;
   debería migrarse a configuración más adelante.
7. **El Daily Brief solo asigna una sección por noticia**, no genera
   las 10 secciones completas de la Parte 3 (eso requiere agregación
   de varias Stories del día, no de una noticia aislada).
8. **Varios valores de `recommendations` en el YAML son asunciones**,
   no confirmaciones de negocio — cada una está marcada con su propio
   `todo` explicando la duda (ver `config/rules/recommendation_rules.yml`).

### Sprint 4 (PR HUB Daily) — TODOs nuevos

9. **La sección Debug se oculta editando código, no con un flag.**
   `daily/html_renderer.py` no expone todavía un parámetro
   `include_debug` — para producción hay que comentar la llamada a
   `_debug_section(...)` en `render_html`. Es una línea, pero conviene
   convertirlo en parámetro antes de automatizar el envío por correo.
10. **"Oportunidades PR" depende de qué reglas estén READY.** Con el
    Rulebook actual (8/15 reglas activas), la mayoría de las
    oportunidades provienen de PR-001 y PR-008; PR-003, PR-005 y PR-009
    —que aportarían más variedad a esta sección— siguen PENDING (ver
    deuda técnica #1-3 arriba). No es un bug del Daily, es el mismo
    Rulebook incompleto propagándose a la nueva vista.
11. **El HTML se verificó con LibreOffice headless y, desde el Sprint
    5, también con Chromium real (Playwright)** — ambos daily_brief.html
    y training_report.html se probaron con captura de pantalla en
    Chromium. Sigue faltando la prueba en un cliente de correo real
    (Gmail/Outlook) antes de confiar en que `daily_brief.html` se vea
    igual de bien ahí que en el navegador — `training_report.html` no
    aplica aquí, no está pensado para enviarse por correo.
12. **Sin envío por correo todavía.** `run_daily.py` solo escribe el
    archivo HTML — conectarlo a un servicio de envío (Resend, Gmail
    API, u otro) es la integración natural siguiente, fuera del
    alcance de este sprint.

## Modo de Entrenamiento (Sprint 5)

Permite validar, noticia por noticia y con casos reales, si el
criterio del Rule Engine coincide con el criterio del Coordinador de
PR — el insumo real para decidir qué reglas del Rulebook ajustar más
adelante.

```bash
python run_training.py
```

Esto:
1. Lee todas las noticias `.json` de `training/examples/` (16 noticias
   reales de julio/agosto 2026, ver más abajo).
2. Corre el pipeline existente sobre cada una — exactamente el mismo
   de `run_daily.py`, sin ninguna modificación.
3. Genera **`training_daily_brief.html`** — el Daily Brief de esas
   noticias, igual que hasta ahora (mismo `daily/aggregator.py` y
   `daily/html_renderer.py` del Sprint 4, sin cambios).
4. Genera **`training_report.html`** — el reporte de validación
   manual, nuevo en este sprint.

Opciones:
```bash
python run_training.py --input otra_carpeta/
```

### El reporte de validación

Para cada noticia, `training_report.html` muestra lo que el sistema
determinó — Titular, Marca detectada, Event Type, Priority, Regla
aplicada, Recommendation Actions — y debajo un control de validación:

```
¿Correcto?  ○ Sí   ○ No
```

Si marcas **No**, se despliegan los campos de corrección (Marca
correcta, Priority correcta, Recommendation correcta, Comentarios). Al
final de la página, el botón **"Descargar validaciones (JSON)"**
exporta todo lo marcado a un archivo local — comparando, para cada
noticia, lo que decidió el sistema contra lo que corregiste. No hay
aprendizaje automático ni envío a ningún servicio: el JavaScript es
local, sin `fetch` ni llamadas de red (verificado explícitamente en
`tests/test_training_report.py`), y el archivo se genera con un `Blob`
en el propio navegador.

Cómo se usa en la práctica: abres `training_report.html`, vas
marcando Sí/No noticia por noticia (idealmente junto con el
Coordinador de PR real), descargas el JSON al terminar, y ese archivo
es el insumo para la siguiente ronda de ajuste del Rulebook — no se
edita `priority_rules.yml` automáticamente a partir de él, eso sigue
siendo una decisión humana.

### `training/examples/` — 16 noticias reales

A diferencia de `data/daily_input/` y `examples/` (Sprints 3 y 4, con
noticias **ficticias** para pruebas), estas 16 son noticias reales de
julio/agosto de 2026, buscadas y verificadas para este sprint, con
`source_url` a la nota original:

| # | Noticia | Fuente | Resultado del sistema |
|---|---|---|---|
| 01 | Alerta SERNAC: Citroën/DS/Fiat/Jeep/Opel/Peugeot, alternador | SERNAC | **HIGH** (PR-001) |
| 02 | Alerta SERNAC: DS/Peugeot, módulo VSM | SERNAC | **HIGH** (PR-001) |
| 03 | Stellantis anuncia plan para fallas PureTech en Chile | Autocosmos | Sin clasificar |
| 04 | Stellantis asume representación directa (ex-Astara) | La Tercera | Sin clasificar |
| 05 | Crédito automotriz Stellantis llega a 45% (Santander Consumer) | BioBioChile | Sin clasificar |
| 06 | Jeep celebra 85 años, expedición Colombia | Autonoticias | Sin clasificar — **marca no detectada** (ver hallazgo abajo) |
| 07 | BYD Yuan Pro llega como híbrido enchufable | Rutamotor | LOW (PR-010) |
| 08 | Buque BYD Changzhou llega a Chile | Autonoticias | Sin clasificar |
| 09 | BAIC presenta BJ81, primera pickup para Chile | Autonoticias | LOW (PR-010) |
| 10 | Campaña "Kia In" entre las más valoradas | Autonoticias | Sin clasificar |
| 11 | Nissan renueva el Versa con Astara | Autonoticias | LOW (PR-010) |
| 12 | Toyota Yaris/Yaris Cross: 2 estrellas en Latin NCAP | Latin NCAP | **HIGH** (PR-013) |
| 13 | ANAC: ventas +5,5% primer semestre, Peugeot lidera comerciales | Emol | MEDIUM (PR-011) |
| 14 | ANAC: descuento en permiso de circulación EV baja a 50% | Emol | MEDIUM (PR-012) |
| 15 | Latin NCAP endurece protocolo de pruebas desde 2026 | Autocosmos | HIGH (PR-013, `event_type` **inferido**) |
| 16 | Marcas chinas llegan a 31% de participación en Chile | Diario Financiero | MEDIUM (PR-011) |

**Dos hallazgos reales surgidos al procesar estas 16 noticias** (no
con las ficticias de los sprints anteriores — solo aparecieron con
texto real):

1. **Bug corregido**: Entity Recognition hacía matching por
   subcadena sin límites de palabra. La noticia de Kia (#10) detectaba
   incorrectamente "DS Automobiles", porque `"ds"` es subcadena de
   `"Ads"` (de "premios Ads People Like") y `"auto"` es subcadena de
   `"automotriz"`. Corregido con `\b` (límites de palabra) en
   `classification/entity_recognition.py`, con test de regresión.
2. **Hallazgo NO corregido, dejado para tu validación**: la noticia
   #06 ("Jeep celebra sus 85 años...") no detecta la marca Jeep en
   absoluto. La razón es la misma protección contra falsos positivos
   que ya existía (Jeep, como palabra genérica en español, exige una
   palabra de contexto como "Wrangler" o "Stellantis" cerca) — pero
   esta noticia real no menciona ningún modelo ni "Stellantis", así
   que el resguardo termina bloqueando una mención legítima. No lo
   arreglé unilateralmente porque cambiar `disambiguationContext` es
   una decisión de configuración de negocio, no un bug de código —
   pero es exactamente el tipo de caso que `training_report.html`
   está pensado para sacar a la luz.

Como ves en la tabla, la mayoría de las 16 noticias reales terminan
"Sin clasificar" — es el reflejo honesto de que el Rulebook v0.2 solo
tiene 8 reglas activas (ver "Estado del Rulebook" más abajo). El
reporte de validación te va a mostrar eso también, no solo lo que
"funciona".

### TODOs del Sprint 5

13. **El JSON exportado no se vuelve a importar a ningún lado.**
    `training_report.html` genera `training_validations.json`, pero no
    existe todavía un paso que lea ese archivo y lo compare
    automáticamente contra `priority_rules.yml`/`recommendation_rules.yml`
    para sugerir qué reglas ajustar. Ese análisis, hoy, es manual.
14. **`training/examples/` es un set fijo, no se actualiza solo.**
    Agregar noticias reales nuevas de meses futuros es un paso manual
    (crear el `.json`, correr `run_training.py` de nuevo) — no hay
    ningún conector ni scraping, tal como pidió este sprint.
15. **La ambigüedad de PR-013 (Latin NCAP) quedó expuesta, no
    resuelta.** La noticia #12 (Toyota, competidor) dispara HIGH igual
    que si fuera una marca Stellantis, porque la regla nunca se acotó
    a marcas propias (ambigüedad ya señalada en la revisión de la
    Parte 2B). El modo de entrenamiento es, de hecho, el lugar
    correcto para decidir si eso está bien o hay que acotar la regla.
16. **El fix de límites de palabra (hallazgo #1 más arriba) tiene un
    efecto secundario, también real, en `data/daily_input` (Sprint 4):
    la palabra de contexto `"camioneta"` (singular) ya no coincide con
    `"camionetas"` (plural) en el texto, porque `\b` exige límite de
    palabra exacto en ambos lados.** Antes del fix, esto "funcionaba"
    por accidente (el mismo tipo de matching laxo que causó el bug del
    hallazgo #1); ahora la fixture `03_investigacion_sernac_ram.json`
    ya no detecta la marca RAM. No se parcheó `brands.yml` para
    agregar la variante plural — es la misma categoría de decisión que
    el caso de Jeep: configuración de negocio, no bug de código,
    queda para revisión humana en vez de corregirse silenciosamente.



```
pr-hub/
├── config/
│   ├── knowledge_base/     # brands, competitors, organizations, models,
│   │                       # technologies, sources, taxonomy, event_types
│   └── rules/              # priority_rules.yml, recommendation_rules.yml
├── knowledge_base/         # Knowledge Base Loader
├── rule_engine/            # Motor genérico: condition, rules, loader, registry, engine
├── classification/         # Entity Recognition + Event Detection
├── models/                 # NewsInput, enums de dominio
├── pipeline/               # Etapas desacopladas + orquestador + factory
├── brief/                  # Daily Brief Generator (funciones puras, por noticia)
├── daily/                  # Sprint 4: agregación + etiquetas + HTML renderer (email-safe)
├── training/               # Sprint 5: reporte de validación manual (report_renderer.py)
│   └── examples/           # 16 noticias REALES de julio/agosto 2026 (input de run_training.py)
├── data/daily_input/       # Sprint 4: noticias ficticias del día (input de run_daily.py)
├── examples/               # Ejemplos ficticios de uso directo con main.py
├── tests/                  # 65 tests + fixtures de noticias ficticias
├── main.py                 # python main.py noticia.json (una noticia)
├── run_daily.py            # python run_daily.py (el día completo -> HTML, noticias ficticias)
├── run_training.py         # python run_training.py (noticias reales -> Daily Brief + reporte de validación)
├── daily_brief.html        # Generado por run_daily.py (incluido como ejemplo)
└── training_report.html    # Generado por run_training.py (incluido como ejemplo)
```

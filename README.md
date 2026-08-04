# Stellantis PR Intelligence Hub — MVP (Sprint 3 + Sprint 4)

Primer MVP funcional del Decision Engine: procesa una noticia y genera
un Daily Brief estructurado, siguiendo el Priority Rulebook v0.2 y las
Decision Matrices ya definidas — sin IA, completamente basado en
reglas.

**Sprint 4 (PR HUB Daily)** agrega la experiencia de usuario real:
`python run_daily.py` procesa las noticias del día y genera
`daily_brief.html`, un correo ejecutivo listo para abrir en el
navegador o pegar en Gmail/Outlook — sin tocar el Rule Engine, la
Knowledge Base ni ningún YAML existente.

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

42 tests del Sprint 3 + 14 tests nuevos de `daily/` (Sprint 4) = **56
tests**, cubriendo: Knowledge Base Loader, Entity Recognition
(incluyendo desambiguación de alias), Event Detection, Rule Engine
(AND/OR/NOT anidados, `single_winner`, `accumulate_all`, reglas
deshabilitadas), pipeline desacoplado, el flujo completo end-to-end
con 10 noticias ficticias, y la agregación/etiquetado del Daily.

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
11. **El HTML se verificó con un conversor headless (LibreOffice), no
    en un navegador real ni en Gmail/Outlook.** El diseño usa tablas +
    estilos inline (la práctica recomendada para compatibilidad de
    email), pero falta la prueba real en un cliente de correo antes de
    confiar en que se vea igual de bien ahí que en el navegador.
12. **Sin envío por correo todavía.** `run_daily.py` solo escribe el
    archivo HTML — conectarlo a un servicio de envío (Resend, Gmail
    API, u otro) es la integración natural siguiente, fuera del
    alcance de este sprint.

## Estructura del proyecto

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
├── daily/                  # Sprint 4: agregación + etiquetas + HTML renderer
├── data/daily_input/       # Sprint 4: noticias ficticias del día (input de run_daily.py)
├── examples/               # Ejemplos de uso directo con main.py
├── tests/                  # 56 tests + fixtures de noticias ficticias
├── main.py                 # python main.py noticia.json (una noticia)
├── run_daily.py            # python run_daily.py (el día completo -> HTML)
└── daily_brief.html        # Generado por run_daily.py (incluido como ejemplo)
```

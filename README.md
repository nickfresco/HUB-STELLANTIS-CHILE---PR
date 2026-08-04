# Stellantis PR Intelligence Hub — MVP (Sprint 3)

Primer MVP funcional del Decision Engine: procesa una noticia y genera
un Daily Brief estructurado, siguiendo el Priority Rulebook v0.2 y las
Decision Matrices ya definidas — sin IA, completamente basado en
reglas.

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

42 tests, cubriendo: Knowledge Base Loader, Entity Recognition
(incluyendo desambiguación de alias), Event Detection, Rule Engine
(AND/OR/NOT anidados, `single_winner`, `accumulate_all`, reglas
deshabilitadas), pipeline desacoplado, y el flujo completo end-to-end
con 10 noticias ficticias.

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

## Deuda técnica declarada (documentada como TODO en el código)

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
├── brief/                  # Daily Brief Generator (funciones puras)
├── tests/                  # 42 tests + fixtures de noticias ficticias
└── main.py
```

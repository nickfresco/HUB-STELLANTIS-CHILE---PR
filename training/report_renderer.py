"""
Training Report Renderer — genera training_report.html: una tabla de
validación manual, noticia por noticia, para comparar el criterio del
Rule Engine contra el criterio real del Coordinador de PR.

Sin aprendizaje automático: el reporte se completa a mano en el
navegador. El único JavaScript incluido es local y sin dependencias
externas — sirve para mostrar/ocultar los campos de corrección según
la respuesta, y para exportar las validaciones ya marcadas a un
archivo JSON descargable (Blob local, sin conexión a ningún servicio).

No reutiliza daily/html_renderer.py a propósito: ese renderer está
optimizado para compatibilidad de correo (Gmail/Outlook); este es una
herramienta de trabajo en navegador, sin esa restricción, por lo que
puede usar CSS moderno y JavaScript sin que ambos objetivos compitan
entre sí dentro del mismo archivo.
"""

from __future__ import annotations
import html
import json
from typing import Any, Dict, List, Optional

from daily.labels import action_label

INK = "#14213D"
PAPER = "#ECEEF2"
SURFACE = "#FFFFFF"
HAIRLINE = "#DADFE6"
MUTED = "#6B7280"
GOOD = "#2E6B52"
BAD = "#B23A32"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def _esc(text: Optional[str]) -> str:
    return html.escape(text or "", quote=True)


def _priority_label(priority: Optional[str]) -> str:
    return priority or "Sin clasificar"


def _card(index: int, brief: Dict[str, Any]) -> str:
    # Sprint 7 (P4): antes solo se mostraba "brand or competitors",
    # descartando en silencio cualquier Organization detectada — causa
    # confirmada de la ambigüedad de la Ronda 1, casos #13 y #14 (el
    # Coordinador escribía el nombre de un organismo en el campo
    # "Marca correcta" porque no tenía dónde más verlo). Ahora se
    # muestran las tres listas del Fact por separado, sin combinar.
    brands = brief.get("brand") or []
    competitors = brief.get("competitors") or []
    organizations = brief.get("organizations") or []

    def _fmt_entities(values: list) -> str:
        return ", ".join(values) if values else "— (ninguna detectada)"

    rules = brief["rules_triggered"]["priority_rules"]
    rule_txt = ", ".join(rules) if rules else "Ninguna"
    why = brief.get("why_it_matters")

    actions = brief.get("recommendations", [])
    actions_txt = ", ".join(action_label(a) for a in actions) if actions else "Ninguna"

    opportunities = brief.get("opportunities") or []
    opportunities_txt = (
        ", ".join(f"{o['type']} (score {o['score']})" for o in opportunities)
        if opportunities else "Ninguna"
    )

    source_name = brief.get("source", {}).get("name", "—")
    source_url = brief.get("source_url")
    source_link = (
        f'<a href="{_esc(source_url)}" target="_blank" rel="noopener" style="color:{INK};">{_esc(source_name)} ↗</a>'
        if source_url else _esc(source_name)
    )

    event_type = brief.get("event_type")
    event_type_txt = f"{_esc(event_type) if event_type else 'Sin detectar'}"
    if brief.get("event_type_source"):
        event_type_txt += f' <span class="muted">({_esc(brief["event_type_source"])})</span>'

    return f"""
<div class="card" data-index="{index}">
  <div class="card-header">
    <div class="story-title">{_esc(brief['story'])}</div>
    <div class="priority-chip">{_esc(_priority_label(brief.get('priority')))}</div>
  </div>
  <div class="muted small">{source_link}</div>

  <table class="fact-table">
    <tr><td class="fact-label">Marcas Stellantis detectadas</td><td>{_esc(_fmt_entities(brands))}</td></tr>
    <tr><td class="fact-label">Competidores detectados</td><td>{_esc(_fmt_entities(competitors))}</td></tr>
    <tr><td class="fact-label">Organismos detectados</td><td>{_esc(_fmt_entities(organizations))}</td></tr>
    <tr><td class="fact-label">Event Type</td><td>{event_type_txt}</td></tr>
    <tr><td class="fact-label">Priority</td><td>{_esc(_priority_label(brief.get('priority')))}</td></tr>
    <tr><td class="fact-label">Regla aplicada</td><td>{_esc(rule_txt)}{f' — <span class="muted">{_esc(why)}</span>' if why else ''}</td></tr>
    <tr><td class="fact-label">Recommendation Actions</td><td>{_esc(actions_txt)}</td></tr>
    <tr><td class="fact-label">Oportunidades detectadas</td><td>{_esc(opportunities_txt)}</td></tr>
  </table>

  <div class="validation">
    <div class="validation-question">¿Correcto?</div>
    <label class="radio-label">
      <input type="radio" name="correct_{index}" value="si" onchange="toggleCorrection({index}, false)"> Sí
    </label>
    <label class="radio-label">
      <input type="radio" name="correct_{index}" value="no" onchange="toggleCorrection({index}, true)"> No
    </label>

    <div id="correction_{index}" class="correction-fields" style="display:none;">
      <label class="field-label">Entidad correcta <span class="muted">(marca, competidor u organismo)</span>
        <input type="text" id="brand_correct_{index}" placeholder="Ej: Peugeot, Toyota, ANAC">
      </label>
      <label class="field-label">Priority correcta
        <select id="priority_correct_{index}">
          <option value="">— sin cambio —</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
          <option value="Ninguna">Ninguna (no debería tener prioridad)</option>
        </select>
      </label>
      <label class="field-label">Recommendation correcta
        <input type="text" id="recommendation_correct_{index}" placeholder="Ej: EvaluarComunicado">
      </label>
      <label class="field-label">Comentarios
        <textarea id="comments_{index}" rows="2" placeholder="¿Qué faltó o qué sobró en el criterio del sistema?"></textarea>
      </label>
    </div>
  </div>
</div>
"""


def _errors_block(errors: List[Dict[str, str]]) -> str:
    if not errors:
        return ""
    rows = "".join(
        f'<li><strong>{_esc(e["file"])}</strong>: {_esc(e["error"])}</li>' for e in errors
    )
    return f"""
<div class="card" style="border-left:4px solid {BAD};">
  <div class="story-title">⚠ {len(errors)} noticia(s) no se pudieron procesar</div>
  <ul class="muted small">{rows}</ul>
</div>
"""


def render_training_report(briefs: List[Dict[str, Any]], errors: List[Dict[str, str]], meta: Dict[str, Any]) -> str:
    cards_html = "".join(_card(i, b) for i, b in enumerate(briefs))
    errors_html = _errors_block(errors)

    # Datos crudos embebidos para que el botón "Descargar validaciones"
    # pueda incluir, junto a lo que marque el Coordinador, lo que el
    # sistema calculó — sin eso, el JSON exportado no serviría para
    # comparar criterio del sistema vs. criterio humano.
    system_data = [
        {
            "index": i,
            "story": b["story"],
            "source": b.get("source", {}).get("name"),
            "source_url": b.get("source_url"),
            "system_brands": b.get("brand") or [],
            "system_competitors": b.get("competitors") or [],
            "system_organizations": b.get("organizations") or [],
            "system_event_type": b.get("event_type"),
            "system_priority": b.get("priority"),
            "system_recommendations": b.get("recommendations", []),
            "system_opportunities": b.get("opportunities") or [],
            "system_rules": b["rules_triggered"]["priority_rules"],
        }
        for i, b in enumerate(briefs)
    ]

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PR HUB — Modo de Entrenamiento</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:0; background:{PAPER}; font-family:{SANS}; color:{INK}; }}
  .wrap {{ max-width: 760px; margin: 0 auto; padding: 32px 20px 80px 20px; }}
  .masthead {{ border-top:2px solid {INK}; border-bottom:1px solid {INK}; padding:14px 0; text-align:center; margin-bottom:18px; }}
  .masthead .eyebrow {{ font-size:12px; letter-spacing:.2em; text-transform:uppercase; font-weight:700; }}
  h1 {{ font-family: Georgia, serif; font-size: 26px; margin: 10px 0 4px 0; }}
  .meta {{ color:{MUTED}; font-size:13px; margin-bottom: 6px; }}
  .instructions {{ background:{SURFACE}; border:1px solid {HAIRLINE}; border-radius:8px; padding:14px 18px; font-size:13.5px; line-height:1.5; margin-bottom:24px; }}
  .card {{ background:{SURFACE}; border:1px solid {HAIRLINE}; border-left:4px solid {INK}; border-radius:8px; padding:16px 18px; margin-bottom:14px; }}
  .card-header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }}
  .story-title {{ font-weight:700; font-size:15px; line-height:1.35; }}
  .priority-chip {{ font-size:10.5px; font-weight:700; letter-spacing:.04em; color:#fff; background:{MUTED}; padding:3px 9px; border-radius:3px; white-space:nowrap; }}
  .muted {{ color:{MUTED}; }}
  .small {{ font-size:12px; }}
  .fact-table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:13px; }}
  .fact-table td {{ padding:5px 0; vertical-align:top; border-bottom:1px solid {PAPER}; }}
  .fact-label {{ color:{MUTED}; width:180px; font-weight:600; }}
  .validation {{ margin-top:14px; padding-top:12px; border-top:1px dashed {HAIRLINE}; }}
  .validation-question {{ font-weight:700; font-size:13px; margin-bottom:6px; }}
  .radio-label {{ margin-right:18px; font-size:13.5px; cursor:pointer; }}
  .correction-fields {{ margin-top:10px; padding:12px; background:{PAPER}; border-radius:6px; display:flex; flex-direction:column; gap:8px; }}
  .field-label {{ font-size:12.5px; color:{MUTED}; display:flex; flex-direction:column; gap:3px; }}
  .field-label input, .field-label select, .field-label textarea {{
    font-family:{SANS}; font-size:13px; color:{INK}; padding:6px 8px; border:1px solid {HAIRLINE}; border-radius:4px; background:{SURFACE};
  }}
  .toolbar {{ position: sticky; bottom: 0; background:{SURFACE}; border-top:1px solid {HAIRLINE}; padding:14px 20px; display:flex; justify-content:space-between; align-items:center; margin-top: 24px; border-radius: 8px; box-shadow: 0 -2px 8px rgba(0,0,0,0.05); }}
  .counter {{ font-size:13px; color:{MUTED}; }}
  button.download {{ background:{INK}; color:#fff; border:none; padding:10px 18px; border-radius:6px; font-size:13.5px; font-weight:600; cursor:pointer; font-family:{SANS}; }}
  button.download:hover {{ opacity:0.9; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    <div class="eyebrow">Stellantis · PR Intelligence</div>
    <h1>Modo de Entrenamiento</h1>
    <div class="meta">{_esc(meta.get('fecha_legible',''))} · {meta.get('noticias_procesadas',0)} noticias procesadas</div>
  </div>

  <div class="instructions">
    Para cada noticia, indica si el criterio del sistema (marca, prioridad, evento y
    recomendaciones) coincide con lo que tú, como Coordinador de PR, habrías determinado.
    Si marcas <strong>No</strong>, completa los campos de corrección. Al final puedes
    descargar todas las validaciones en un archivo JSON — no se envía a ningún servidor,
    el archivo se genera y descarga localmente en tu navegador.
  </div>

  {errors_html}
  {cards_html}

  <div class="toolbar">
    <span class="counter" id="counter">0 de {len(briefs)} validadas</span>
    <button class="download" onclick="downloadValidations()">Descargar validaciones (JSON)</button>
  </div>
</div>

<script>
const SYSTEM_DATA = {json.dumps(system_data, ensure_ascii=False)};

function toggleCorrection(index, show) {{
  document.getElementById('correction_' + index).style.display = show ? 'flex' : 'none';
  updateCounter();
}}

function updateCounter() {{
  let count = 0;
  const total = SYSTEM_DATA.length;
  for (let i = 0; i < total; i++) {{
    const radios = document.getElementsByName('correct_' + i);
    for (const r of radios) {{
      if (r.checked) {{ count++; break; }}
    }}
  }}
  document.getElementById('counter').textContent = count + ' de ' + total + ' validadas';
}}

function downloadValidations() {{
  const results = SYSTEM_DATA.map(item => {{
    const i = item.index;
    const radios = document.getElementsByName('correct_' + i);
    let correct = null;
    for (const r of radios) {{ if (r.checked) correct = (r.value === 'si'); }}

    return {{
      ...item,
      validated: correct !== null,
      correct: correct,
      brand_correct: correct === false ? document.getElementById('brand_correct_' + i).value : null,
      priority_correct: correct === false ? document.getElementById('priority_correct_' + i).value : null,
      recommendation_correct: correct === false ? document.getElementById('recommendation_correct_' + i).value : null,
      comments: correct === false ? document.getElementById('comments_' + i).value : null,
    }};
  }});

  const blob = new Blob([JSON.stringify(results, null, 2)], {{ type: 'application/json' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'training_validations.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}}

document.querySelectorAll('input[type=radio]').forEach(r => r.addEventListener('change', updateCounter));
</script>
</body>
</html>
"""

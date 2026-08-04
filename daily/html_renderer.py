"""
Daily HTML Renderer.

Dirección de diseño (Sprint 4):
  - Masthead estilo "cable de inteligencia" (serif, versalitas, doble
    filete) en vez del típico hero genérico — es el elemento que hace
    que esto se sienta como un briefing ejecutivo, no un dashboard.
  - Paleta fría (ink navy + gris paper), NO el cliché cálido crema+serif
    +terracota. Un color de acento distinto por sección (Flash=rojo,
    Stellantis=verde, Competencia=azul, Industria=grafito,
    Oportunidades=ámbar), consistente con los emojis pedidos.
  - Tipografía: Georgia (serif) para masthead y encabezados de sección;
    stack sans-serif de sistema para cuerpo — ambas son fuentes
    "seguras" para email (no dependen de fuentes web externas).
  - HTML basado en tablas con estilos inline (no depende de que el
    cliente de correo respete <style> en <head>) — funciona en Gmail y
    Outlook, no solo en navegador.

Todo el texto es generado por plantilla (daily/labels.py) o proviene
directamente de los datos ya calculados por el Rule Engine — cero IA.
"""

from __future__ import annotations
import html
from typing import Any, Dict, List, Optional

from daily.labels import action_label

# ---------------------------------------------------------------------
# Tokens de diseño
# ---------------------------------------------------------------------
INK = "#14213D"
PAPER = "#ECEEF2"
SURFACE = "#FFFFFF"
HAIRLINE = "#DADFE6"
MUTED = "#6B7280"

ACCENTS = {
    "flash": "#B23A32",
    "stellantis": "#2E6B52",
    "competencia": "#33587E",
    "industria": "#5B6472",
    "oportunidad": "#B8862E",
}

SERIF = "Georgia, 'Times New Roman', Times, serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def _esc(text: Optional[str]) -> str:
    return html.escape(text or "", quote=True)


def _eyebrow(text: str, color: str = MUTED) -> str:
    return (
        f'<div style="font-family:{SANS};font-size:11px;font-weight:700;'
        f'letter-spacing:.09em;text-transform:uppercase;color:{color};">{_esc(text)}</div>'
    )


def _priority_chip(priority: Optional[str]) -> str:
    labels = {"HIGH": ("ALTA", "#B23A32"), "CRITICAL": ("CRÍTICA", "#8C1F1A"),
              "MEDIUM": ("MEDIA", "#B8862E"), "LOW": ("BAJA", "#5B6472")}
    text, color = labels.get(priority or "", ("SIN CLASIFICAR", MUTED))
    return (
        f'<span style="display:inline-block;font-family:{SANS};font-size:10px;font-weight:700;'
        f'letter-spacing:.06em;color:#ffffff;background:{color};padding:3px 8px;border-radius:3px;">'
        f'{text}</span>'
    )


def _action_chip(label: str) -> str:
    return (
        f'<span style="display:inline-block;font-family:{SANS};font-size:11px;color:{INK};'
        f'background:{PAPER};border:1px solid {HAIRLINE};padding:3px 9px;border-radius:12px;'
        f'margin:2px 4px 2px 0;">{_esc(label)}</span>'
    )


# ---------------------------------------------------------------------
# Bloques
# ---------------------------------------------------------------------

def _masthead(meta: Dict[str, Any]) -> str:
    fecha = _esc(meta.get("fecha_legible", ""))
    hora = _esc(meta.get("hora_generacion", ""))
    n = meta.get("noticias_procesadas", 0)
    t = meta.get("tiempo_ejecucion_segundos", 0)
    return f"""
<tr><td style="padding:0 0 18px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td style="border-top:2px solid {INK};border-bottom:1px solid {INK};padding:14px 0;text-align:center;">
      <div style="font-family:{SERIF};font-size:13px;letter-spacing:.28em;text-transform:uppercase;color:{INK};font-weight:700;">
        Stellantis &nbsp;·&nbsp; PR Intelligence
      </div>
    </td></tr>
  </table>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:12px;">
    <tr>
      <td style="font-family:{SERIF};font-size:26px;font-weight:700;color:{INK};padding:0;">
        Daily Brief
      </td>
      <td align="right" style="font-family:{SANS};font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:.05em;">
        {fecha}
      </td>
    </tr>
  </table>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:6px;">
    <tr><td style="font-family:{SANS};font-size:12px;color:{MUTED};">
      Generado {hora} &nbsp;·&nbsp; {n} noticias procesadas &nbsp;·&nbsp; {t:.1f}s de ejecución
    </td></tr>
  </table>
</td></tr>
"""


def _resumen_ejecutivo(bullets: List[str]) -> str:
    items = "".join(
        f'<tr><td style="padding:5px 0;font-family:{SANS};font-size:14.5px;line-height:1.5;color:{INK};">'
        f'<span style="color:{ACCENTS["oportunidad"]};font-weight:700;">— </span>{_esc(b)}</td></tr>'
        for b in bullets
    )
    return f"""
<tr><td style="padding:22px 0 6px 0;">
  {_eyebrow("Resumen Ejecutivo", INK)}
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;background:{SURFACE};border:1px solid {HAIRLINE};border-radius:8px;padding:14px 18px;">
    {items}
  </table>
</td></tr>
"""


def _section_title(emoji: str, title: str, color: str, count: Optional[int] = None) -> str:
    count_txt = f' <span style="color:{MUTED};font-weight:400;">({count})</span>' if count is not None else ""
    return f"""
<tr><td style="padding:26px 0 10px 0;border-top:1px solid {HAIRLINE};">
  <div style="font-family:{SERIF};font-size:17px;font-weight:700;color:{INK};">
    <span style="color:{color};">{emoji}</span>&nbsp; {_esc(title)}{count_txt}
  </div>
</td></tr>
"""


def _flash_card(brief: Dict[str, Any]) -> str:
    brand_txt = ", ".join(brief.get("brand") or brief.get("competitors") or ["—"])
    actions = "".join(_action_chip(action_label(a)) for a in brief.get("recommendations", []))
    why = _esc(brief.get("why_it_matters") or "Cumple criterio de prioridad alta según el Rulebook vigente.")
    return f"""
<tr><td style="padding:0 0 12px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background:{SURFACE};border:1px solid {HAIRLINE};border-left:4px solid {ACCENTS['flash']};border-radius:6px;">
    <tr><td style="padding:14px 16px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="font-family:{SANS};font-size:15px;font-weight:700;color:{INK};line-height:1.35;">
            {_esc(brief['story'])}
          </td>
          <td align="right" valign="top" style="white-space:nowrap;padding-left:10px;">{_priority_chip(brief.get('priority'))}</td>
        </tr>
      </table>
      <div style="font-family:{SANS};font-size:11.5px;color:{MUTED};margin-top:4px;">
        {_esc(brand_txt)} &nbsp;·&nbsp; {_esc(brief.get('source', {}).get('name', '—'))}
      </div>
      <div style="font-family:{SANS};font-size:13px;color:{INK};line-height:1.5;margin-top:8px;">
        {_esc(brief.get('summary', ''))}
      </div>
      <div style="font-family:{SANS};font-size:12.5px;color:{INK};line-height:1.5;margin-top:8px;padding:8px 10px;background:{PAPER};border-radius:5px;">
        <strong>¿Por qué importa?</strong> {why}
      </div>
      <div style="margin-top:10px;">{actions}</div>
    </td></tr>
  </table>
</td></tr>
"""


def _brand_card(brief: Dict[str, Any], accent: str, commentary_key: Optional[str] = None) -> str:
    medio = _esc(brief.get("source", {}).get("name", "—"))
    actions = "".join(_action_chip(action_label(a)) for a in brief.get("recommendations", []))
    commentary = ""
    if commentary_key and brief.get(commentary_key):
        label = "Por qué es un benchmark útil" if commentary_key == "benchmark_commentary" else "Por qué importa para Stellantis"
        commentary = (
            f'<div style="font-family:{SANS};font-size:12px;color:{INK};line-height:1.5;margin-top:7px;'
            f'padding:7px 10px;background:{PAPER};border-radius:5px;">'
            f'<strong>{label}:</strong> {_esc(brief[commentary_key])}</div>'
        )
    return f"""
<tr><td style="padding:0 0 10px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background:{SURFACE};border:1px solid {HAIRLINE};border-left:3px solid {accent};border-radius:6px;">
    <tr><td style="padding:12px 15px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="font-family:{SANS};font-size:14px;font-weight:600;color:{INK};line-height:1.35;">
            {_esc(brief['story'])}
          </td>
          <td align="right" valign="top" style="white-space:nowrap;padding-left:10px;">{_priority_chip(brief.get('priority'))}</td>
        </tr>
      </table>
      <div style="font-family:{SANS};font-size:11px;color:{MUTED};margin-top:3px;">{medio}</div>
      <div style="font-family:{SANS};font-size:12.5px;color:{INK};line-height:1.5;margin-top:6px;">
        {_esc(brief.get('summary', ''))}
      </div>
      {commentary}
      <div style="margin-top:8px;">{actions}</div>
    </td></tr>
  </table>
</td></tr>
"""


def _brand_group_block(brand: str, briefs: List[Dict[str, Any]], accent: str, commentary_key: Optional[str] = None) -> str:
    header = (
        f'<tr><td style="padding:10px 0 6px 0;">'
        f'<div style="font-family:{SANS};font-size:12.5px;font-weight:700;color:{accent};'
        f'text-transform:uppercase;letter-spacing:.04em;">{_esc(brand)}</div></td></tr>'
    )
    cards = "".join(_brand_card(b, accent, commentary_key) for b in briefs)
    return header + cards


def _oportunidades(opportunities: List[Dict[str, Any]]) -> str:
    if not opportunities:
        return (
            f'<tr><td style="padding:8px 0;font-family:{SANS};font-size:13px;color:{MUTED};font-style:italic;">'
            f'Sin oportunidades accionables identificadas hoy.</td></tr>'
        )
    rows = ""
    for i, opp in enumerate(opportunities, start=1):
        rows += f"""
<tr><td style="padding:9px 0;border-bottom:1px solid {HAIRLINE};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td width="26" valign="top" style="font-family:{SERIF};font-size:14px;color:{ACCENTS['oportunidad']};font-weight:700;">{i:02d}</td>
      <td style="font-family:{SANS};font-size:13.5px;color:{INK};line-height:1.5;">
        <strong>{_esc(opp['action_label'])}</strong> — {_esc(opp['story'])}
        <span style="color:{MUTED};"> ({_esc(opp['brand'])})</span>
      </td>
    </tr>
  </table>
</td></tr>
"""
    return rows


def _resumen_del_dia(counts: Dict[str, int]) -> str:
    labels = [
        ("Flash Alerts", counts["flash_alerts"], ACCENTS["flash"]),
        ("Stellantis", counts["stellantis"], ACCENTS["stellantis"]),
        ("Competencia", counts["competencia"], ACCENTS["competencia"]),
        ("Industria", counts["industria"], ACCENTS["industria"]),
        ("Oportunidades", counts["oportunidades"], ACCENTS["oportunidad"]),
    ]
    cells = "".join(
        f'<td width="20%" align="center" style="padding:14px 4px;">'
        f'<div style="font-family:{SERIF};font-size:24px;font-weight:700;color:{color};">{count}</div>'
        f'<div style="font-family:{SANS};font-size:10.5px;color:{MUTED};text-transform:uppercase;letter-spacing:.05em;margin-top:2px;">{label}</div>'
        f'</td>'
        for label, count, color in labels
    )
    return f"""
<tr><td style="padding:0 0 6px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background:{SURFACE};border:1px solid {HAIRLINE};border-radius:8px;">
    <tr>{cells}</tr>
  </table>
</td></tr>
"""


def _debug_section(briefs: List[Dict[str, Any]], errors: List[Dict[str, str]]) -> str:
    rows = ""
    for b in briefs:
        rules = ", ".join(b["rules_triggered"]["priority_rules"] + b["rules_triggered"]["recommendation_rules"]) or "—"
        actions = ", ".join(b.get("recommendations", [])) or "—"
        rows += f"""
<tr>
  <td style="padding:5px 6px;border-bottom:1px solid {HAIRLINE};font-family:{SANS};font-size:11px;color:{INK};">{_esc(b['story'][:60])}</td>
  <td style="padding:5px 6px;border-bottom:1px solid {HAIRLINE};font-family:{SANS};font-size:11px;color:{INK};">{_esc(', '.join(b.get('brand') or b.get('competitors') or []))}</td>
  <td style="padding:5px 6px;border-bottom:1px solid {HAIRLINE};font-family:{SANS};font-size:11px;color:{INK};">{_esc(b.get('event_type'))} <span style="color:{MUTED};">({_esc(b.get('event_type_source'))})</span></td>
  <td style="padding:5px 6px;border-bottom:1px solid {HAIRLINE};font-family:{SANS};font-size:11px;color:{INK};">{_esc(b.get('priority'))}</td>
  <td style="padding:5px 6px;border-bottom:1px solid {HAIRLINE};font-family:{SANS};font-size:11px;color:{INK};">{_esc(rules)}</td>
  <td style="padding:5px 6px;border-bottom:1px solid {HAIRLINE};font-family:{SANS};font-size:11px;color:{INK};">{_esc(actions)}</td>
</tr>
"""
    error_rows = "".join(
        f'<tr><td colspan="6" style="padding:5px 6px;font-family:{SANS};font-size:11px;color:{ACCENTS["flash"]};">'
        f'⚠ {_esc(e["file"])}: {_esc(e["error"])}</td></tr>'
        for e in errors
    )
    return f"""
<tr><td style="padding:22px 0 40px 0;">
  <details>
    <summary style="font-family:{SANS};font-size:12px;color:{MUTED};cursor:pointer;padding:8px 0;border-top:1px dashed {HAIRLINE};">
      🧠 Debug (solo desarrollo) — {len(briefs)} noticias, {len(errors)} errores
    </summary>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;">
      <tr style="background:{PAPER};">
        <td style="padding:5px 6px;font-family:{SANS};font-size:10px;color:{MUTED};text-transform:uppercase;">Story</td>
        <td style="padding:5px 6px;font-family:{SANS};font-size:10px;color:{MUTED};text-transform:uppercase;">Brand</td>
        <td style="padding:5px 6px;font-family:{SANS};font-size:10px;color:{MUTED};text-transform:uppercase;">Event Type</td>
        <td style="padding:5px 6px;font-family:{SANS};font-size:10px;color:{MUTED};text-transform:uppercase;">Priority</td>
        <td style="padding:5px 6px;font-family:{SANS};font-size:10px;color:{MUTED};text-transform:uppercase;">Rule IDs</td>
        <td style="padding:5px 6px;font-family:{SANS};font-size:10px;color:{MUTED};text-transform:uppercase;">Actions</td>
      </tr>
      {rows}
      {error_rows}
    </table>
  </details>
</td></tr>
"""


# ---------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------

def render_html(digest: Dict[str, Any], all_briefs: List[Dict[str, Any]], errors: List[Dict[str, str]]) -> str:
    meta = digest["meta"]

    flash_html = "".join(_flash_card(b) for b in digest["flash_alerts"]) or (
        f'<tr><td style="padding:8px 0;font-family:{SANS};font-size:13px;color:{MUTED};font-style:italic;">'
        f'Sin alertas de prioridad alta hoy.</td></tr>'
    )

    stellantis_html = "".join(
        _brand_group_block(brand, items, ACCENTS["stellantis"]) for brand, items in digest["stellantis"]
    ) or f'<tr><td style="padding:8px 0;font-family:{SANS};font-size:13px;color:{MUTED};font-style:italic;">Sin novedades de marcas Stellantis hoy.</td></tr>'

    competencia_html = "".join(
        _brand_group_block(brand, items, ACCENTS["competencia"], commentary_key="benchmark_commentary")
        for brand, items in digest["competencia"]
    ) or f'<tr><td style="padding:8px 0;font-family:{SANS};font-size:13px;color:{MUTED};font-style:italic;">Sin movimientos de competencia relevantes hoy.</td></tr>'

    industria_html = "".join(
        _brand_card(b, ACCENTS["industria"], commentary_key="industry_commentary") for b in digest["industria"]
    ) or f'<tr><td style="padding:8px 0;font-family:{SANS};font-size:13px;color:{MUTED};font-style:italic;">Sin noticias de industria hoy.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stellantis PR Intelligence — Daily Brief</title>
<style>
  @media only screen and (max-width: 640px) {{
    .container {{ width: 100% !important; }}
    .pad {{ padding-left: 16px !important; padding-right: 16px !important; }}
  }}
  a {{ color: {INK}; }}
</style>
</head>
<body style="margin:0;padding:0;background:{PAPER};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{PAPER};">
<tr><td align="center" style="padding:28px 12px;">
  <table role="presentation" class="container" width="640" cellpadding="0" cellspacing="0" border="0" style="width:640px;max-width:100%;">
    <tr><td class="pad" style="padding:0 22px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        {_masthead(meta)}
        {_resumen_ejecutivo(digest["resumen_ejecutivo"])}

        {_section_title("🔴", "Flash Alerts", ACCENTS["flash"], digest["counts"]["flash_alerts"])}
        {flash_html}

        {_section_title("🟢", "Stellantis", ACCENTS["stellantis"], digest["counts"]["stellantis"])}
        {stellantis_html}

        {_section_title("🔵", "Competencia", ACCENTS["competencia"], digest["counts"]["competencia"])}
        {competencia_html}

        {_section_title("⚪", "Industria", ACCENTS["industria"], digest["counts"]["industria"])}
        {industria_html}

        {_section_title("💡", "Oportunidades PR", ACCENTS["oportunidad"], digest["counts"]["oportunidades"])}
        {_oportunidades(digest["oportunidades"])}

        {_section_title("📊", "Resumen del día", INK)}
        {_resumen_del_dia(digest["counts"])}

        <tr><td style="padding:22px 0 4px 0;border-top:1px solid {HAIRLINE};font-family:{SANS};font-size:10.5px;color:{MUTED};text-align:center;">
          Stellantis PR Intelligence Hub — generado automáticamente, basado en reglas. No reemplaza el criterio del Coordinador de PR.
        </td></tr>

        {_debug_section(all_briefs, errors)}
      </table>
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>
"""

"""Genera U04_E08_Jhonatan_Cabral.pdf y U04_E08_Evidencias_Jhonatan_Cabral.pdf a partir de los artefactos del repositorio.
Uso: uv run --with reportlab --with pillow python scripts/build_e08_pdf.py"""
import csv
import json
import re
import textwrap
from pathlib import Path

import numpy as np
import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Image, KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table)

PROJECT = Path(__file__).resolve().parents[1]
EVIDENCE = PROJECT / "reports/e08/evidencias"
OUT_MAIN, OUT_EVID = PROJECT / "U04_E08_Jhonatan_Cabral.pdf", PROJECT / "U04_E08_Evidencias_Jhonatan_Cabral.pdf"

FONTS = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial", FONTS / "arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", FONTS / "arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", FONTS / "ariali.ttf"))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", FONTS / "arialbi.ttf"))
pdfmetrics.registerFont(TTFont("Consolas", FONTS / "consola.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-BoldItalic")

BLUE = colors.HexColor("#1F4E79")
NAVY = colors.HexColor("#1F3E66")
GRAY = colors.HexColor("#595959")
RULE = colors.HexColor("#B4C3D6")
LABEL_BG = colors.HexColor("#EEF2F7")
HIGHLIGHT = colors.HexColor("#FFF4D6")
REPO = "https://github.com/prodintdata/Ciencia-de-datos-II"
FOLDER = "Unidad%20%20IV/Ejercicio%2008"
REPO_URL = f"{REPO}/tree/main/{FOLDER}"
EVID_URL = f"{REPO}/blob/main/{FOLDER}/U04_E08_Evidencias_Jhonatan_Cabral.pdf"

body = ParagraphStyle("body", fontName="Arial", fontSize=9.5, leading=12.6, alignment=4, spaceAfter=5)
small = ParagraphStyle("small", parent=body, fontSize=8.3, leading=10.4, alignment=0, spaceAfter=0)
cell = ParagraphStyle("cell", parent=small)
tiny = ParagraphStyle("tiny", parent=small, fontSize=7.8, leading=9.6)
head = ParagraphStyle("head", parent=small, fontName="Arial-Bold", textColor=colors.white)
title = ParagraphStyle("title", fontName="Arial-Bold", fontSize=19, leading=23, textColor=BLUE, alignment=TA_CENTER)
subtitle = ParagraphStyle("subtitle", fontName="Arial", fontSize=10.5, leading=13, textColor=GRAY, alignment=TA_CENTER, spaceAfter=10)
h1 = ParagraphStyle("h1", fontName="Arial-Bold", fontSize=13.5, leading=17, textColor=BLUE, spaceBefore=10, spaceAfter=2, keepWithNext=1)
ev_title = ParagraphStyle("ev_title", parent=small, fontName="Arial-Bold", fontSize=9.2, leading=11.5, spaceAfter=3)
ev_text = ParagraphStyle("ev_text", parent=small, fontSize=8.6, leading=11)
code = ParagraphStyle("code", fontName="Consolas", fontSize=7.0, leading=8.8, backColor=colors.HexColor("#F3F3F3"),
                      borderPadding=5, spaceBefore=4, spaceAfter=8)
hanging = ParagraphStyle("ref", parent=body, leftIndent=18, firstLineIndent=-18, alignment=0)
WIDTH = letter[0] - 1.5 * inch


def p(text, style=body):
    return Paragraph(text, style)


def link(url, text):
    return f'<link href="{url}"><u><font color="#1F4E79">{text}</font></u></link>'


def section(text):
    rule = HRFlowable(width="100%", thickness=0.8, color=RULE, spaceBefore=0, spaceAfter=5)
    rule.keepWithNext = 1
    return [p(text, h1), rule]


def table(rows, widths, highlight_rows=(), style_cell=cell):
    data = [[p(str(c), head) for c in rows[0]]] + [[p(str(c), style_cell) for c in row] for row in rows[1:]]
    style = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, RULE),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 5)]
    style += [("BACKGROUND", (0, r), (-1, r), HIGHLIGHT) for r in highlight_rows]
    return Table(data, colWidths=[w * WIDTH for w in widths], style=style, repeatRows=1, spaceBefore=3, spaceAfter=7)


def label_table(rows, label_width=0.2):
    data = [[p(f"{a}", cell), p(b, cell)] for a, b in rows]
    style = [("BACKGROUND", (0, 0), (0, -1), LABEL_BG), ("GRID", (0, 0), (-1, -1), 0.4, RULE),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    return Table(data, colWidths=[label_width * WIDTH, (1 - label_width) * WIDTH], style=style, spaceAfter=8)


def footer_for(code_name):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Arial", 7.5)
        canvas.setFillColor(GRAY)
        canvas.drawString(0.75 * inch, 0.5 * inch, f"INF-8239, {code_name}. Jhonatan Cabral, BE2322")
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Página {doc.page}")
        canvas.restoreState()
    return footer


def read_csv(path):
    with open(PROJECT / path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path):
    return json.loads((PROJECT / path).read_text(encoding="utf-8"))


f3 = lambda v: "—" if v in ("", None) else f"{np.round(float(v), 3):.3f}"

# ---------------------------------------------------------------- datos (todo se lee de los artefactos)
gates = yaml.safe_load((PROJECT / "configs/governance.yml").read_text(encoding="utf-8"))["gates"]
mon = yaml.safe_load((PROJECT / "configs/monitoring.yml").read_text(encoding="utf-8"))
retention = read_csv("student_inputs/retention_policy.csv")
raci, handoffs = read_csv("student_inputs/raci.csv"), read_csv("student_inputs/handoffs.csv")
decision = read_json("reports/lab13/deployment_decision.json")
month = {r["month"]: r for r in read_csv("reports/e08/monitoring_by_month.csv")}
month_eg = {r["month"]: r for r in read_csv("reports/e08/monitoring_by_month_expgrad.csv")}
drill = read_json("reports/e08/incident_drill/timeline.json")
d_base, d_inc = read_json("reports/e08/incident_drill/decision_baseline.json"), read_json("reports/e08/incident_drill/decision_incident.json")
d_rec = read_json("reports/e08/incident_drill/decision_recovered.json")
manifest = read_json("reports/e08/incident_drill/manifest.json")
profile = {r["zone"]: r for r in read_csv("reports/e08/incident_drill/batch_profile.csv")}
fair_inc = {r["protected_group"]: r for r in read_csv("reports/e08/incident_drill/fairness_incident.csv")}
fair_lab13 = {r["protected_group"]: r for r in read_csv("reports/lab13/fairness_by_group.csv")}
rec = decision["recommendation"]
fpr_rev = read_json("reports/e08/fpr_gap_review.json")
eg_status, base_status = fpr_rev["status"]["expgrad_tpr_parity"], fpr_rev["status"]["logistic_base"]
assert eg_status["status"] == "REVIEW" and "fpr_gap@2026-11" in eg_status["failed"]
assert fpr_rev["max_fpr_gap"] == gates["max_fpr_gap"]
# Test count comes from the real console output, so the PDF cannot claim more than what ran.
run_log = (PROJECT / "reports/e08/run_log.txt").read_text(encoding="utf-8")
n_tests = int(re.search(r"(\d+) passed", run_log).group(1))
assert "failed" not in run_log.split("$ uv run python")[0]
assert decision["decision"]["status"] == "GO" and d_inc["decision"]["status"] == "REVIEW" and d_rec["decision"]["status"] == "GO"
assert month["2026-11"]["support_ok"] == "True"

story = []
# ---------------------------------------------------------------- portada
story += [p("Ejercicio 08: Expediente de gobernanza y simulacro", title),
          p("INF-8239 Ciencia de Datos II, Unidad 04 (U04.E08)", subtitle),
          label_table([
              ("Estudiante", "Jhonatan Cabral"),
              ("Matrícula", "BE2322"),
              ("Repositorio", f'{link(REPO_URL, "github.com/prodintdata/Ciencia-de-datos-II")}, Unidad IV/Ejercicio 08'),
              ("Evidencia", f'{link(EVID_URL, "U04_E08_Evidencias_Jhonatan_Cabral.pdf")} (abrir en GitHub)'),
              ("Base", "LAB13, proyecto INF8239_U04_Gobernanza_DSS_Proyecto_Base_uv"),
              ("Decisión final", "<b>REVIEW</b>: se mantiene la tolerancia y no se recomienda aún el modelo mitigado (sección 6)"),
          ])]
story.append(p("<b>Caso.</b> El Territorial Review DSS prioriza casos territoriales sintéticos para revisión humana. Solo recomienda "
               "un orden y presenta evidencia; la decisión es humana. Las cifras de este informe se leen de los archivos editables del "
               "repositorio (CSV, YAML y JSON)."))

# ---------------------------------------------------------------- 1. normativa
story += section("1. Obligación legal, marco voluntario y recomendación ética")
story.append(p("Cada afirmación lleva su fundamento. «Ley» es la Ley núm. 172-13 sobre la Protección de Datos de Carácter Personal "
               "(13 de diciembre de 2013); «Const.» es la Constitución de la República Dominicana. Las obligaciones legales solo se "
               "activarían con datos reales; lo que no tiene base en una norma se marca como marco voluntario o criterio propio."))
story.append(table([
    ["Afirmación", "Fundamento", "Tipo"],
    ["Con datos sintéticos la ley no se activa: no hay personas identificadas ni identificables",
     "Ley, art. 2 (se aplica a datos de carácter personal) y art. 6.9 y 6.16 (definición de dato personal y de persona identificable)",
     "Obligación legal (no aplica)"],
    ["Con datos reales, <i>age_band</i>, <i>zone</i> y los conteos serían datos personales si se asocian a una persona identificable",
     "Ley, art. 6.9 y 6.16", "Obligación legal"],
    ["<i>protected_group</i> sería dato especialmente protegido solo si revela origen racial o étnico; en ese caso nadie puede ser "
     "obligado a darlo y solo se trata con consentimiento libre o interés general autorizado por ley, o con fines estadísticos sin identificar al titular",
     "Ley, art. 6.8 (datos especialmente protegidos) y art. 75", "Obligación legal"],
    ["Se necesita base legal: consentimiento libre, expreso y consciente, salvo excepción (funciones propias del Estado, obligación legal o disociación)",
     "Ley, art. 5.4 (consentimiento) y art. 27.2 y 27.9 (excepciones)", "Obligación legal"],
    ["Aviso a las personas sobre finalidad, destinatarios, responsable y derechos",
     "Ley, art. 5.3 (derecho de información)", "Obligación legal"],
    ["Minimización: solo campos adecuados, pertinentes y no excesivos para la finalidad",
     "Ley, art. 5.8 (finalidad) y art. 5.2.a (calidad)", "Obligación legal"],
    ["Acceso, rectificación y supresión; acción judicial de hábeas data",
     "Ley, arts. 10, 14 y 17; Const., art. 44 (intimidad, citado por el art. 1 de la Ley) y art. 70 (hábeas data)", "Obligación legal"],
    ["Acceso restringido a <i>protected_group</i> y evidencia de incidentes sin filas de casos",
     "Ley, art. 5.5 (seguridad) y art. 5.6 (deber de secreto)", "Obligación legal"],
    ["Retención de 24 meses (<i>retention_policy.csv</i>)",
     "La Ley no fija un plazo general (el art. 64 solo regula reportes crediticios). El plazo es criterio propio, derivado de la finalidad "
     "(art. 5.8) y del derecho de supresión con bloqueo (arts. 14 y 15)", "Criterio propio"],
    ["Medir brechas entre grupos",
     "Const., art. 39 (derecho a la igualdad) justifica vigilarlas. Ninguna norma citada fija la tolerancia de 0.16: es criterio propio "
     "(LAB12). Una brecha observada no prueba discriminación", "Criterio propio"],
    ["Revisión humana de todos los casos y vía de apelación",
     "La Ley no regula decisiones automatizadas. Se adoptan por NIST AI RMF 1.0 (GOVERN y MANAGE)", "Marco voluntario y ética"],
    ["RACI, inventario, monitoreo, runbook, Model Card y Datasheet",
     "NIST AI RMF 1.0 (GOVERN, MAP, MEASURE, MANAGE); Mitchell et al. (2019); Gebru et al. (2021)", "Marco voluntario"],
    [f"Brechas solo con {mon['min_support']} o más casos por grupo; decisión sobre la brecha de FPR de noviembre (sección 6)",
     "Criterio propio, con intervalo bootstrap en <i>reports/e08/fpr_gap_review.json</i>", "Recomendación ética"],
], [0.4, 0.43, 0.17], style_cell=tiny))

# ---------------------------------------------------------------- 2. inventario
story += section("2. Inventario, minimización y retención")
story.append(table([
    ["Campos", "Uso", "Minimización"],
    ["name, document_number, email, phone", "Ninguno", "No se recolectan; el contrato rechaza el lote antes de predecir"],
    ["case_id, received_date", "Trazabilidad y corte temporal", "Fuera del modelo; la fecha se agrega a mes en el monitoreo"],
    ["protected_group", "Solo auditoría de equidad", "Fuera del modelo; acceso restringido al equipo de auditoría"],
    ["age_band", "Modelo y auditoría", "Tramos de edad, no fecha de nacimiento"],
    ["zone, previous_incidents, infrastructure_score, exposure", "Modelo", "4 zonas amplias; conteos e índices agregados; zone se vigila como proxy"],
    ["target", "Entrenamiento y evaluación", "Resultado de la revisión humana"],
], [0.36, 0.22, 0.42]))
story.append(table([["Artefacto", "Retención", "Responsable"]] +
                   [[r["artifact"], r["retention"], r["owner"]] for r in retention], [0.38, 0.4, 0.22], style_cell=tiny))
story.append(p("Detalle por campo en <i>student_inputs/data_inventory.csv</i> y por artefacto en <i>student_inputs/retention_policy.csv</i>. "
               "Una prueba verifica que el inventario coincida con el contrato de datos y con las variables del modelo."))

# ---------------------------------------------------------------- 3. datasheet y model card
story += section("3. Datasheet y Model Card trazables")
story.append(p(f"<i>docs/DATASET_CARD.md</i> describe motivación, composición (640 casos, 0 faltantes), preprocesamiento, usos y "
               f"retención. <i>docs/MODEL_CARD.md</i> registra la versión <b>{rec['model_version']}</b>, las puertas, los grupos, el "
               "monitoreo y el simulacro. Cada cifra apunta a su archivo de origen."))
story.append(table([
    ["Puerta", "Valor", "Umbral", "Resultado"],
    ["Recall global", f3(decision["metrics"]["recall"]), f"≥ {gates['min_recall']}", "Pasa"],
    ["Brecha de recall", f3(decision["gaps"]["recall_gap"]), f"≤ {gates['max_recall_gap']}", "Pasa"],
    ["Brecha de FPR", f3(decision["gaps"]["fpr_gap"]), f"≤ {gates['max_fpr_gap']}", "Pasa"],
    ["Latencia y tamaño", f"{decision['resources']['latency_ms']:.2f} ms; {decision['resources']['model_kb']:.1f} KB",
     f"≤ {gates['max_latency_ms']} ms; ≤ {gates['max_model_kb']} KB", "Pasa"],
    ["Recall G1 (vigilancia)", f3(fair_lab13["G1"]["recall"]), "0.68", "<b>Bajo</b>"],
], [0.3, 0.25, 0.27, 0.18], highlight_rows=(5,)))

# ---------------------------------------------------------------- 4. RACI y traspasos
story += section("4. RACI y traspaso entre roles")
story.append(p("Cada actividad tiene un solo Accountable (<i>student_inputs/raci.csv</i>). Los traspasos "
               "(<i>student_inputs/handoffs.csv</i>) definen entregable, criterio de aceptación y firma; una prueba exige que firme "
               "el Accountable de la actividad y que la evidencia exista."))
story.append(table([["Traspaso", "De → a", "Firma (Accountable)"]] +
                   [[h["stage"], f"{h['from_role']} → {h['to_role']}", h["sign_off"]] for h in handoffs],
                   [0.24, 0.48, 0.28], style_cell=tiny))

# ---------------------------------------------------------------- 5. monitoreo, runbook y simulacro
story += section("5. Monitoreo, runbook y simulacro")
story.append(p("<i>configs/monitoring.yml</i> define señales, frecuencia, responsable y acción. Resultado mensual del periodo de prueba "
               "con el modelo base y con el modelo mitigado de E07 (EG):"))
rows = [["Mes", "n (G1/G2)", "Recall", "Brecha recall", "Brecha FPR", "Brecha recall EG", "Brecha FPR EG"]]
for m in ("2026-10", "2026-11", "2026-12"):
    a, b = month[m], month_eg[m]
    gap = (lambda v: f3(v)) if a["support_ok"] == "True" else (lambda v: f"<i>{f3(v)}</i>*")
    rows.append([m, f"{a['n']} ({a['n_G1']}/{a['n_G2']})", f3(a["recall"]), gap(a["recall_gap"]), gap(a["fpr_gap"]),
                 gap(b["recall_gap"]), gap(b["fpr_gap"])])
story.append(table(rows, [0.1, 0.14, 0.1, 0.15, 0.14, 0.19, 0.18], highlight_rows=(2,)))
story.append(p(f"* Menos de {mon['min_support']} casos en un grupo: no se interpreta. Octubre tiene recall {f3(month['2026-10']['recall'])} "
               f"(&lt; {gates['min_recall']}) y noviembre una brecha de recall de {f3(month['2026-11']['recall_gap'])} (&gt; {gates['max_recall_gap']}). "
               f"El modelo mitigado la reduce a {f3(month_eg['2026-11']['recall_gap'])}, pero la brecha de FPR sube a {f3(month_eg['2026-11']['fpr_gap'])} "
               f"(&gt; {gates['max_fpr_gap']}) y su recall de octubre es {f3(month_eg['2026-10']['recall'])}. La decisión sobre esa brecha está en la sección 6.", tiny))
story.append(p(f"<b>Simulacro</b> (<i>scripts/e08_incident_drill.py</i>): {drill['scenario']}."))
story.append(table([
    ["Métrica", "Lote correcto", "Lote con fallo", "Lote corregido"],
    ["Recall global", f3(d_base["metrics"]["recall"]), f3(d_inc["metrics"]["recall"]), f3(d_rec["metrics"]["recall"])],
    ["Brecha de recall", f3(d_base["gaps"]["recall_gap"]), f3(d_inc["gaps"]["recall_gap"]), f3(d_rec["gaps"]["recall_gap"])],
    ["Recall G1 / G2", f"{f3(fair_lab13['G1']['recall'])} / {f3(fair_lab13['G2']['recall'])}",
     f"{f3(fair_inc['G1']['recall'])} / {f3(fair_inc['G2']['recall'])}", f"{f3(fair_lab13['G1']['recall'])} / {f3(fair_lab13['G2']['recall'])}"],
    ["Decisión", d_base["decision"]["status"], f"<b>{d_inc['decision']['status']}</b> ({', '.join(d_inc['decision']['failed'])})", d_rec["decision"]["status"]],
], [0.25, 0.22, 0.31, 0.22], highlight_rows=(4,)))
story.append(table([
    ["Fase", "Resultado"],
    ["Detección", f"Contrato: un lote con <i>email</i> fue rechazado. PSI global {f3(drill['psi_previous_incidents'])} (no alcanza 0.25); "
     f"ceros en Oeste: {100 * float(profile['Oeste']['share_zero_reference']):.0f} % en la referencia frente a "
     f"{100 * float(profile['Oeste']['share_zero_batch']):.0f} % en el lote. Las puertas pasan a REVIEW"],
    ["Contención y rollback", "REVIEW, cola en FIFO y lote en cuarentena (runbook). Con el lote corregido vuelve a GO; la reactivación requiere firma de la Dirección"],
    ["Evidencia", f"{len(manifest['files'])} archivos con SHA-256, versión y hash del modelo, sin filas de casos (<i>reports/e08/incident_drill/</i>)"],
    ["Comunicación", "Interna y a representantes de personas afectadas, según el runbook (<i>docs/RUNBOOK.md</i>)"],
    ["Postmortem", "Causa, impacto y acciones con responsable y fecha (<i>reports/e08/POSTMORTEM.md</i>)"],
], [0.22, 0.78], style_cell=tiny))

# ---------------------------------------------------------------- 6. decisión
story += section("6. Decisión final")
fg, bs = fpr_rev["fpr"], fpr_rev["bootstrap"]
story.append(p(f"<b>Brecha de FPR de noviembre.</b> Noviembre es el único mes con soporte suficiente. Allí el modelo mitigado (EG) tiene "
               f"una brecha de FPR de {f3(fpr_rev['fpr_gap'])}, por encima de la tolerancia de {fpr_rev['max_fpr_gap']}: G1 recibe "
               f"{fg['G1']['false_positives']} alertas falsas en {fg['G1']['negatives']} negativos (FPR {f3(fg['G1']['value'])}) y G2 "
               f"{fg['G2']['false_positives']} en {fg['G2']['negatives']} (FPR {f3(fg['G2']['value'])}). El intervalo bootstrap del 95 % va de "
               f"{f3(bs['ci95'][0])} a {f3(bs['ci95'][1])} y el {100 * bs['share_above_limit']:.0f} % de las remuestras supera el límite "
               f"(<i>reports/e08/fpr_gap_review.json</i>). Con 6 negativos en G2, un solo caso mueve la FPR de G2 en 0.167: la evidencia "
               "no confirma ni descarta la brecha."))
story.append(table([
    ["Opción ante la brecha", "Decisión", "Justificación"],
    ["Mantener REVIEW", "<b>Sí</b>",
     f"La política de monitoreo dice «puerta fallida = REVIEW» y la condición de retiro de LAB11 incluye la brecha de FPR &gt; 0.16. "
     f"EG falla {', '.join(eg_status['failed'])}; el modelo base también queda en REVIEW ({', '.join(base_status['failed'])}). "
     "Ninguna versión puede operar como recomendación"],
    ["Cambiar la política", "No",
     "Subir la tolerancia después de ver el resultado sería ajustar la regla al modelo. Además, el daño no es menor: las alertas falsas "
     "recaen sobre G1, el grupo protegido, como escrutinio extra no justificado. Un cambio futuro solo se haría antes de ver datos nuevos, "
     "con firma de la Dirección y consulta a los representantes de personas afectadas"],
    ["Descartar EG", "No, por ahora",
     "En todo el periodo de prueba EG tiene brecha de FPR 0.101 y menor FPR que el modelo base en ambos grupos; en noviembre difiere de él "
     "en un caso por grupo. Se descarta si, con 20 o más negativos por grupo, la brecha de FPR sigue por encima de 0.16"],
], [0.2, 0.13, 0.67], highlight_rows=(1,)))
story.append(table([
    ["Opción de despliegue", "Decisión", "Razón"],
    ["Desplegar", "No", "El GO agregado oculta fallas por mes; ambas versiones fallan puertas mensuales, y un fallo de ingesta baja el "
     f"recall a {f3(d_inc['metrics']['recall'])}. Los datos son sintéticos"],
    ["Modificar", "<b>Sí</b>", "EG sigue como candidato, con regla de calidad de datos por zona y monitoreo mensual con los denominadores "
     "(positivos y negativos) por grupo"],
    ["Limitar", "<b>Sí</b>", "La cola opera con FIFO, el respaldo del runbook. EG corre solo en sombra: calcula su orden, pero los analistas no lo ven"],
    ["No utilizar", "No, por ahora", "Se aplica si se cumple la condición de retiro de LAB11 tras la revisión del 2026-11-30"],
], [0.2, 0.13, 0.67], highlight_rows=(2, 3)))
story.append(p("<b>Condición para salir de REVIEW:</b> un mes con 20 o más casos por grupo y 20 o más negativos por grupo en que EG "
               "cumpla las tres puertas (recall ≥ 0.68 y brechas de recall y FPR ≤ 0.16). La Dirección de Gestión de Riesgo Territorial "
               "(Accountable) firma el despliegue, la suspensión y la reactivación."))

# ---------------------------------------------------------------- 7. pruebas y git
story += section("7. Pruebas y Git")
story.append(p(f"{n_tests} pruebas aprobadas: contrato de datos, privacidad, equidad, gobernanza, app, inventario, retención, traspasos, "
               "monitoreo y simulacro. El historial de commits y las etiquetas <i>u04-lab13</i> y <i>u04-e08</i> están en el "
               "repositorio. La salida de consola está en <i>reports/e08/run_log.txt</i> y en el anexo."))
story.append(Preformatted("uv sync --frozen\nuv run pytest -q\nuv run python scripts/e08_monitoring.py\nuv run python scripts/e08_incident_drill.py", code))

# ---------------------------------------------------------------- 8. IA
story += section("8. Uso de inteligencia artificial")
story.append(label_table([
    ("Herramienta", "Claude Code (Claude Opus 5.5, de Anthropic) en Visual Studio Code, octubre y noviembre de 2026."),
    ("Mi trabajo", "Ejecuté LAB13 y E08 en mi equipo y tomé las capturas (E1–E7). Definí el alcance, las tolerancias, la retención, "
     "los traspasos y la decisión de mantener REVIEW ante la brecha de FPR de noviembre. Revisé cada propuesta antes de aceptarla, "
     "ejecuté las pruebas y los scripts, verifiqué las citas legales e hice los commits, las etiquetas y el push."),
    ("Uso de la IA", "Le pedí verificar el laboratorio contra el manual, proponer código (monitoreo, simulacro, pruebas y generador "
     "del PDF), ubicar los artículos de la Ley 172-13 y diagnosticar errores de Git. Ajusté lo que propuso."),
    ("Verificación", f"Las {n_tests} pruebas pasan. Las cifras del informe se leen de los CSV y JSON, y las comparé con <i>run_log.txt</i>."),
    ("Correcciones", "Ajusté la alerta mensual con poco soporte, añadí el perfil por zona al simulacro, recorté una cuenta corporativa "
     "de las capturas y corregí cifras de la Model Card, el datasheet y el postmortem."),
    ("Responsabilidad", "Los valores y las conclusiones son míos. Puedo explicar cada parte y asumo la responsabilidad de lo entregado."),
], label_width=0.2))

# ---------------------------------------------------------------- 9. referencias
story += section("9. Referencias")
story += [
    p("Constitución de la República Dominicana. (2015). Arts. 39, 44 y 70.", hanging),
    p("Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., &amp; Crawford, K. (2021). Datasheets for "
      "datasets. <i>Communications of the ACM, 64</i>(12), 86–92. https://doi.org/10.1145/3458723", hanging),
    p("Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., &amp; Gebru, T. (2019). "
      "Model cards for model reporting. En <i>Proceedings of the Conference on Fairness, Accountability, and Transparency</i> (pp. 220–229). "
      "https://doi.org/10.1145/3287560.3287596", hanging),
    p("National Institute of Standards and Technology. (2023). <i>Artificial Intelligence Risk Management Framework (AI RMF 1.0)</i> "
      "(NIST AI 100-1). https://doi.org/10.6028/NIST.AI.100-1", hanging),
    p("República Dominicana. (2013). <i>Ley núm. 172-13 sobre la Protección de Datos de Carácter Personal</i>. Congreso Nacional, "
      "promulgada el 13 de diciembre de 2013. Arts. 2, 5, 6, 10, 14, 15, 17, 27, 64 y 75.", hanging),
]

doc = SimpleDocTemplate(str(OUT_MAIN), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.7 * inch,
                        bottomMargin=0.8 * inch, title="U04.E08 · Expediente de gobernanza y simulacro",
                        author="Jhonatan Cabral")
doc.build(story, onFirstPage=footer_for("U04.E08"), onLaterPages=footer_for("U04.E08"))
print("PDF:", OUT_MAIN)


# ================================================================ anexo de evidencias
def evidence(name, heading, text):
    image = Image(str(EVIDENCE / name))
    scale = WIDTH / image.imageWidth
    image.drawWidth, image.drawHeight = image.imageWidth * scale, image.imageHeight * scale
    box = Table([[p(heading, ev_title)], [p(text, ev_text)]], colWidths=[WIDTH],
                style=[("BACKGROUND", (0, 0), (-1, -1), LABEL_BG), ("BOX", (0, 0), (-1, -1), 0.4, RULE),
                       ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 7)])
    return KeepTogether([image, Spacer(1, 4), box, Spacer(1, 14)])


ev = [p("Anexo de evidencias · Ejercicio 08", title),
      p("INF-8239 Ciencia de Datos II, Unidad 04 (U04.E08)", subtitle),
      label_table([
          ("Estudiante", "Jhonatan Cabral (BE2322)"),
          ("Informe", f'{link(f"{REPO}/blob/main/{FOLDER}/U04_E08_Jhonatan_Cabral.pdf", "U04_E08_Jhonatan_Cabral.pdf")}'),
          ("Qué contiene", "Capturas de la ejecución de LAB13 en mi equipo (E1–E7) y la salida de consola de E08 (E8)."),
      ])]
ev += section("Capturas de LAB13 · Gobernanza y DSS responsable")
ev.append(p("Ejecuté LAB13 en VS Code el 31 de octubre de 2026. Solo recorté la barra de estado inferior de E1, E2, E3 y E7, que "
            "mostraba datos de una cuenta corporativa; el terminal no se modificó."))
ev.append(evidence("E1.png", "E1. Pruebas y comprobación del entorno al iniciar LAB13",
    "<b>Qué se realiza:</b> <i>uv run pytest -q</i> da 12 pruebas aprobadas. <i>check_environment.py</i> confirma "
    "<i>dataset_status: valid</i>, con 640 filas y 9 columnas. En el explorador está abierta <i>raci.csv</i>, el primer paso de LAB13."))
ev.append(evidence("E2.png", "E2. Pipeline de gobernanza (lab13_governance.py)",
    "<b>Qué se realiza:</b> el pipeline valida la RACI, entrena, audita y evalúa las cinco puertas. Resultado: <i>GO</i> con "
    "<i>failed: []</i>. Es la fuente de la sección 3 del informe."))
ev.append(evidence("E3.png", "E3. Simulacro de LAB13 (simulate_incident.py)",
    "<b>Qué se realiza:</b> el script del curso genera <i>reports/lab13/INCIDENT_POSTMORTEM.md</i> como plantilla con campos REPLACE, "
    "completada después. En E08 se complementa con un simulacro reproducible (sección 5 del informe y E8)."))
ev.append(evidence("E4.png", "E4. Inicio del tablero (streamlit run app.py)",
    "<b>Qué se realiza:</b> Streamlit levanta el servidor en el puerto 8501 y avisa que <i>use_container_width</i> está obsoleto; se "
    "corrigió en <i>app.py</i>."))
ev.append(evidence("E5.png", "E5. Tablero del DSS en el navegador",
    "<b>Qué se realiza:</b> la app muestra el aviso de caso sintético, el propósito, los usos prohibidos, accuracy 0.719, recall 0.717, "
    "decisión GO, métricas por grupo y puertas. Después se añadió la recomendación con versión, política, evidencia y acción humana."))
ev.append(evidence("E6.png", "E6. Pruebas al cerrar LAB13",
    f"<b>Qué se realiza:</b> 19 pruebas aprobadas. Con las correcciones posteriores y E08 pasan a {n_tests} (E8)."))
ev.append(evidence("E7.png", "E7. Preparación de la publicación (uv export)",
    "<b>Qué se realiza:</b> el primer intento falla por un comando incompleto; el segundo resuelve 55 paquetes y genera "
    "<i>requirements.txt</i> sin dependencias de desarrollo ni secretos."))
ev += section("E8. Salida de consola de E08")
ev.append(p("<b>Qué se realiza:</b> pruebas, comprobación del entorno, pipeline de gobernanza, monitoreo mensual y simulacro. Texto "
            "copiado sin cambios de <i>reports/e08/run_log.txt</i>."))
# Long console lines are wrapped (not cut) so no output is lost at the page margin.
wrapped = "\n".join("\n    ".join(textwrap.wrap(line, 128, drop_whitespace=False)) or line
                    for line in run_log.replace("\r", "").strip().splitlines())
ev.append(Preformatted(wrapped, code))
ev.append(p("<b>Manifiesto de evidencia del simulacro</b> (<i>reports/e08/incident_drill/manifest.json</i>):", ev_title))
ev.append(Preformatted(json.dumps(manifest, indent=2), code))

doc = SimpleDocTemplate(str(OUT_EVID), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.7 * inch,
                        bottomMargin=0.8 * inch, title="U04.E08 · Anexo de evidencias", author="Jhonatan Cabral")
doc.build(ev, onFirstPage=footer_for("U04.E08 · Anexo de evidencias"), onLaterPages=footer_for("U04.E08 · Anexo de evidencias"))
print("PDF:", OUT_EVID)

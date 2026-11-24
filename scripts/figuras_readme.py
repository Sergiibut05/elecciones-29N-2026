"""Genera las figuras del README a partir de resultados_29N.xlsx (y del propio notebook).

Uso (desde la raíz del proyecto, después de ejecutar el notebook):
    python scripts/figuras_readme.py

Crea/actualiza los PNG de la carpeta img/.
"""
from pathlib import Path
import base64
import json
import re

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

RAIZ = Path(__file__).resolve().parents[1]
XLSX = RAIZ / "resultados_29N.xlsx"
NOTEBOOK = RAIZ / "Elecciones_29N_modelo_bayesiano.ipynb"
IMG = RAIZ / "img"
IMG.mkdir(exist_ok=True)

# ---------------------------------------------------------------- estilo común
COLORES = {"PP": "#1d84ce", "PSOE": "#e30613", "Vox": "#5ac035", "FA": "#c0367a", "FV": "#f18a00",
           "Sumar": "#c0367a", "Podemos": "#6b2e68", "SALF": "#7a5c3a", "ERC": "#f4b400", "Junts": "#20c0b2",
           "Bildu": "#2b8a3e", "PNV": "#2a7a4a", "BNG": "#76b6e4", "CCa": "#ffd700", "AA": "#3aa357", "OTROS": "#9e9e9e"}
NOMBRE = {"FA": "Frente Amplio", "FV": "Compromís–FV", "AA": "Adelante Andalucía", "CCa": "Coalición Canaria",
          "SALF": "Se Acabó La Fiesta", "Bildu": "EH Bildu"}
TINTA, TINTA_2, TINTA_3 = "#1f2328", "#57606a", "#8c959f"
GRIS_PISTA, GRIS_REJILLA, FONDO = "#eaeef2", "#e6e8eb", "#ffffff"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11, "text.color": TINTA,
    "axes.edgecolor": TINTA_3, "axes.labelcolor": TINTA_2, "xtick.color": TINTA_2, "ytick.color": TINTA_2,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": FONDO, "axes.facecolor": FONDO,
    "savefig.facecolor": FONDO, "savefig.dpi": 160, "savefig.bbox": "tight", "savefig.pad_inches": 0.25,
})


def titulo(fig, texto, sub=None, y=1.0):
    fig.text(0.0, y, texto, fontsize=17, fontweight="bold", color=TINTA, ha="left", va="bottom", transform=fig.transFigure)
    if sub:
        fig.text(0.0, y - 0.012, sub, fontsize=11.5, color=TINTA_2, ha="left", va="top", transform=fig.transFigure)


def guardar(fig, nombre):
    fig.savefig(IMG / nombre)
    plt.close(fig)
    print("  ✓", nombre)


def pct(x):
    return f"{x:.0%}".replace("%", " %")


def rango(s):
    a, b = re.split(r"[–-]", str(s))
    return int(a), int(b)


X = pd.read_excel(XLSX, sheet_name=None)
esc = X["escanos_base"].set_index(X["escanos_base"].columns[0])
bloques = X["bloques_base"].set_index("bloque")
replay = X["replay_errores"].set_index("error como en")
casas = X["efectos_casa"].set_index(X["efectos_casa"].columns[0])
bt = X["backtest_2023_escanos"].set_index("partido")
bt_res = X["backtest_2023_resumen"].set_index("variante")


# ------------------------------------------------------------ 1. hemiciclo
def hemiciclo():
    # escenario mediano; los escaños que no cuadran con 350 se muestran como «en el aire»
    orden = ["FA", "FV", "Podemos", "AA", "BNG", "Bildu", "ERC", "PSOE", "PNV", "Junts", "CCa", "PP", "Vox", "SALF"]
    med = esc["esc_mediana"].reindex(orden).fillna(0).astype(int)
    med = med[med > 0]
    en_aire = 350 - int(med.sum())
    # coloca el bloque «en el aire» en el centro político (entre PSOE y PP)
    asientos = []
    for p, n in med.items():
        if p == "PP" and en_aire > 0:
            asientos += ["?"] * en_aire
        asientos += [p] * n

    # 350 puntos en filas concéntricas, ordenados por ángulo (de izquierda a derecha)
    filas, r0, r1 = 13, 0.42, 1.0
    radios = np.linspace(r0, r1, filas)
    total_long = radios.sum()
    por_fila = np.round(radios / total_long * 350).astype(int)
    por_fila[-1] += 350 - por_fila.sum()
    pts = []
    for r, n in zip(radios, por_fila):
        ang = np.linspace(np.pi, 0, n)
        pts += [(a, r) for a in ang]
    pts.sort(key=lambda t: (-t[0], t[1]))
    xy = np.array([(r * np.cos(a), r * np.sin(a)) for a, r in pts])

    fig, ax = plt.subplots(figsize=(8.6, 6.6))
    cols = [COLORES.get(p, "#ffffff") for p in asientos]
    vacio = np.array([p == "?" for p in asientos])
    ax.scatter(xy[~vacio, 0], xy[~vacio, 1], s=62, c=np.array(cols)[~vacio], edgecolors="white", linewidths=1.2, zorder=3)
    ax.scatter(xy[vacio, 0], xy[vacio, 1], s=62, c="white", edgecolors=TINTA_3, linewidths=1.2, zorder=3)
    ax.plot([0, 0], [r0 - 0.08, r1 + 0.06], color=TINTA, lw=1.2, ls=(0, (3, 3)), zorder=2)
    ax.text(0, r1 + 0.08, "176 = mayoría absoluta", ha="center", va="bottom", fontsize=10.5, color=TINTA)
    ax.text(0, 0.03, "350", ha="center", va="bottom", fontsize=34, fontweight="bold", color=TINTA)
    ax.text(0, -0.02, "escaños", ha="center", va="top", fontsize=12, color=TINTA_2)

    # leyenda con números (identidad nunca solo por color)
    leyenda = [(p, n) for p, n in med.sort_values(ascending=False).items()]
    if en_aire:
        leyenda.append(("?", en_aire))
    x0, y0, dx = -1.02, -0.20, 0.0
    colx = [-1.02, -0.36, 0.30]
    for i, (p, n) in enumerate(leyenda):
        cx, cy = colx[i % 3], y0 - 0.085 * (i // 3)
        if p == "?":
            ax.scatter(cx, cy, s=90, c="white", edgecolors=TINTA_3, linewidths=1.2)
            ax.text(cx + 0.04, cy, f"{n}  en el aire (escaños muy disputados)", va="center", fontsize=10.5, color=TINTA_2)
        else:
            ax.scatter(cx, cy, s=90, c=COLORES[p], edgecolors="white", linewidths=1)
            ax.text(cx + 0.04, cy, f"{n}", va="center", fontsize=11.5, fontweight="bold", color=TINTA)
            ax.text(cx + 0.06 + 0.032 * len(str(n)), cy, NOMBRE.get(p, p), va="center", fontsize=10.5, color=TINTA_2)
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(y0 - 0.085 * ((len(leyenda) - 1) // 3) - 0.08, 1.2)
    ax.set_aspect("equal"); ax.axis("off")
    titulo(fig, "Así quedaría el Congreso en el escenario más probable",
           "Mediana de 20.000 elecciones simuladas · 29-N 2026", y=0.98)
    guardar(fig, "hemiciclo.png")


# ----------------------------------------------------- 2. preguntas clave
def probabilidades():
    preguntas = [
        ("¿Suman PP + Vox mayoría absoluta (176)?", bloques.loc["PP + Vox", "probabilidad"]),
        ("¿Es el PP el partido con más escaños?", bloques.loc["PP primera fuerza en escaños", "probabilidad"]),
        ("¿Suma 176 el bloque de la investidura de 2023\n(PSOE, socios y Junts)?", bloques.loc["Bloque investidura 2023 con Junts", "probabilidad"]),
        ("¿Suman 176 PSOE + FA + Compromís + Podemos?", bloques.loc["PSOE + FA + FV + Podemos", "probabilidad"]),
    ]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    y = np.arange(len(preguntas))[::-1]
    for yi, (q, p) in zip(y, preguntas):
        ax.barh(yi, 1, height=0.42, color=GRIS_PISTA, zorder=1)
        ax.barh(yi, max(p, 0.004), height=0.42, color="#3d5a80", zorder=2)
        ax.text(-0.02, yi, q, ha="right", va="center", fontsize=12, color=TINTA)
        ax.text(1.02, yi, pct(p), ha="left", va="center", fontsize=17, fontweight="bold", color=TINTA)
        n10 = int(round(p * 10))
        ax.text(1.02, yi - 0.33, f"≈ {n10} de cada 10" if n10 else "< 1 de cada 10", ha="left", va="center", fontsize=9.5, color=TINTA_2)
    ax.set_xlim(0, 1); ax.set_ylim(-0.6, len(preguntas) - 0.4); ax.axis("off")
    titulo(fig, "Las preguntas que importan, en probabilidades",
           "Porcentaje de las 20.000 simulaciones en las que ocurre cada cosa", y=0.98)
    fig.subplots_adjust(left=0.42, right=0.86)
    guardar(fig, "probabilidades.png")


# ------------------------------------------------------- 3. rangos de escaños
def rangos():
    t = esc.copy()
    t = t[t["esc_mediana"] + t["esc_media"] > 0.5].sort_values("esc_media")
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for i, (p, r) in enumerate(t.iterrows()):
        a95, b95 = rango(r["esc_IC95"]); a80, b80 = rango(r["esc_IC80"])
        c = COLORES.get(p, "#999")
        ax.plot([a95, b95], [i, i], color=c, lw=2, alpha=.45, solid_capstyle="round")
        ax.plot([a80, b80], [i, i], color=c, lw=9, alpha=.9, solid_capstyle="round")
        ax.scatter(r["esc_mediana"], i, s=70, color="white", edgecolor=TINTA, lw=1.5, zorder=4)
        ax.text(b95 + 2.5, i, f"{int(r['esc_mediana'])}  ({a80}–{b80})", va="center", fontsize=10.5, color=TINTA)
    ax.set_yticks(range(len(t))); ax.set_yticklabels([NOMBRE.get(p, p) for p in t.index], fontsize=11)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 195); ax.set_xlabel("Escaños")
    ax.grid(axis="x", color=GRIS_REJILLA, lw=.8); ax.set_axisbelow(True); ax.spines["left"].set_visible(False)
    # mini leyenda de lectura
    ly = -1.3
    ax.plot([118, 138], [ly, ly], color=TINTA_3, lw=9, solid_capstyle="round", clip_on=False)
    ax.plot([110, 146], [ly, ly], color=TINTA_3, lw=2, alpha=.5, clip_on=False)
    ax.scatter(128, ly, s=70, color="white", edgecolor=TINTA, lw=1.5, zorder=5, clip_on=False)
    ax.text(150, ly, "○ más probable · barra gruesa: 8 de cada 10 · línea fina: 95 de cada 100",
            va="center", fontsize=9.5, color=TINTA_2, clip_on=False)
    ax.set_ylim(-1.8, len(t) - 0.4)
    titulo(fig, "¿Cuántos escaños puede sacar cada partido?",
           "Escaños más probables y rango en el que caen 8 de cada 10 simulaciones", y=0.98)
    guardar(fig, "rangos_escanos.png")


# ------------------------------------------------------ 4. sesgo encuestadoras
def sesgo_encuestadoras():
    s = casas["PP−PSOE"].sort_values()
    lim = 4.2
    fig, ax = plt.subplots(figsize=(10, 8.6))
    y = np.arange(len(s))
    for yi, (casa, v) in zip(y, s.items()):
        c = COLORES["PP"] if v > 0 else COLORES["PSOE"]
        vv = float(np.clip(v, -lim, lim))
        ax.barh(yi, vv, height=0.68, color=c, alpha=.9)
        medio = casas.loc[casa, "medios"] if "medios" in casas and isinstance(casas.loc[casa, "medios"], str) else ""
        etiqueta = f"{casa}" + (f"  ·  {medio}" if medio and medio != "—" else "")
        ax.text(-lim - 0.15 if v > 0 else 0.15, yi, etiqueta, va="center",
                ha="right" if v > 0 else "left", fontsize=9.5, color=TINTA_2)
        txt = "0,0" if abs(v) < 0.05 else f"{v:+.1f}".replace(".", ",").replace("-", "−")
        if abs(v) > lim:
            ax.text(vv + 0.12 if v < 0 else vv - 0.12, yi, f"{txt}  (fuera de escala)", va="center",
                    ha="left" if v < 0 else "right", fontsize=9.5, color="white", fontweight="bold")
        else:
            ax.text(vv + (0.1 if v > 0 else -0.1), yi, txt, va="center", ha="left" if v > 0 else "right", fontsize=9, color=TINTA)
    ax.axvline(0, color=TINTA, lw=1)
    ax.set_xlim(-lim - 3.6, lim + 0.6); ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xticks(range(-4, 5)); ax.set_xlabel("Puntos de diferencia PP − PSOE frente a la encuestadora privada media")
    ax.grid(axis="x", color=GRIS_REJILLA, lw=.8); ax.set_axisbelow(True)
    ax.text(-0.15, len(s) - 0.1, "← da más al PSOE", ha="right", va="bottom", fontsize=11, color=COLORES["PSOE"], fontweight="bold")
    ax.text(0.15, len(s) - 0.1, "da más al PP →", ha="left", va="bottom", fontsize=11, color=COLORES["PP"], fontweight="bold")
    ax.set_ylim(-0.7, len(s) + 0.6)
    titulo(fig, "Cada encuestadora tiene su «acento»",
           "Sesgo estimado por el modelo (efecto casa) en la distancia PP − PSOE. El modelo lo descuenta.", y=0.98)
    guardar(fig, "sesgo_encuestadoras.png")


# ------------------------------------------------------ 5. ¿y si fallan?
def y_si_fallan():
    nombres = {"BASE (error aleatorio)": "Escenario base", "2015": "…como en 2015", "2016": "…como en 2016",
               "April 2019": "…como en abril 2019", "November 2019": "…como en noviembre 2019", "2023": "…como en 2023"}
    orden = ["BASE (error aleatorio)", "2015", "2016", "April 2019", "November 2019", "2023"]
    r = replay.reindex(orden)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    y = np.arange(len(r))[::-1]
    lo, hi = 160, 210
    ax.axvspan(175.5, hi, color="#1d84ce", alpha=.06, lw=0)
    ax.axvline(175.5, color=TINTA, lw=1.2, ls=(0, (3, 3)))
    ax.text(176.2, len(r) - 0.35, "mayoría absoluta →", fontsize=10, color=TINTA, va="center")
    for yi, (k, row) in zip(y, r.iterrows()):
        v = row["PP+Vox (mediana)"]; p = row["P(PP+Vox ≥176)"]
        c = COLORES["PP"] if v >= 176 else TINTA_3
        ax.plot([lo, v], [yi, yi], color=GRIS_PISTA, lw=2, zorder=1)
        ax.scatter(v, yi, s=150, color=c, edgecolor="white", lw=2, zorder=3)
        derecha = v >= 176 and v < 205
        ax.text(v + (1.4 if derecha else -1.4), yi + 0.02, f"{int(v)}", va="center", fontsize=11, fontweight="bold",
                ha="left" if derecha else "right", color=TINTA)
        ax.text(hi + 1.5, yi, pct(p), va="center", fontsize=12, fontweight="bold", color=TINTA)
    ax.text(hi + 1.5, len(r) - 0.35, "prob. mayoría", va="center", fontsize=9.5, color=TINTA_2)
    ax.set_yticks(y); ax.set_yticklabels([nombres[k] for k in r.index], fontsize=11.5)
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.set_xlim(lo, hi); ax.set_ylim(-0.6, len(r) - 0.1); ax.set_xlabel("Escaños de PP + Vox (mediana)")
    ax.grid(axis="x", color=GRIS_REJILLA, lw=.8); ax.set_axisbelow(True)
    titulo(fig, "¿Y si las encuestas fallan como en otras elecciones?",
           "Escaños de PP + Vox si este año se repitiera exactamente el error de las encuestas de cada elección pasada", y=0.98)
    guardar(fig, "y_si_fallan.png")


# ------------------------------------------------------ 6. prueba con 2023
def prueba_2023():
    ps = ["PP", "PSOE", "Vox", "Sumar"]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    for i, p in enumerate(ps):
        a, b = rango(bt.loc[p, "IC80"])
        c = COLORES[p]
        ax.plot([a, b], [i, i], color=c, lw=12, alpha=.35, solid_capstyle="round")
        ax.scatter(bt.loc[p, "mediana"], i, s=90, color="white", edgecolor=c, lw=2.2, zorder=3)
        ax.scatter(bt.loc[p, "real"], i, s=130, marker="X", color=TINTA, edgecolor="white", lw=1, zorder=4)
        ax.text(b + 3, i, f"predicho {int(bt.loc[p, 'mediana'])} · real {int(bt.loc[p, 'real'])}", va="center", fontsize=10.5, color=TINTA)
    ax.set_yticks(range(len(ps))); ax.set_yticklabels(ps, fontsize=12); ax.invert_yaxis()
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 215); ax.set_xlabel("Escaños")
    ax.grid(axis="x", color=GRIS_REJILLA, lw=.8); ax.set_axisbelow(True)
    ax.text(0, 4.05, "○ predicción más probable   ✖ resultado real   barra: rango de 8 de cada 10 simulaciones",
            fontsize=9.5, color=TINTA_2, va="top")
    ax.set_ylim(4.3, -0.6)
    titulo(fig, "Examen sorpresa: el modelo aplicado a las elecciones de 2023",
           "Con solo la información disponible el 18 de julio de 2023: el resultado real cae dentro de todos los rangos", y=0.98)
    guardar(fig, "prueba_2023.png")


# ------------------------------------------- 7. tendencia (desde el notebook)
def tendencia_desde_notebook():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for c in nb["cells"]:
        if c["cell_type"] == "code" and "Intención de voto latente" in "".join(c["source"]):
            for o in c.get("outputs", []):
                if "image/png" in o.get("data", {}):
                    (IMG / "tendencia.png").write_bytes(base64.b64decode(o["data"]["image/png"]))
                    print("  ✓ tendencia.png (copiada del notebook)")
                    return
    print("  ! No se encontró la gráfica de tendencia en el notebook (¿se ejecutó?)")


# ------------------------------------------------------------- 8-9. mapas
GEOJSON = RAIZ / "data" / "provincias_espana.geojson"
# provincia (nombre usado en el notebook) → código INE
INE = {"A Coruña": "15", "Álava": "01", "Albacete": "02", "Alicante": "03", "Almería": "04", "Asturias": "33", "Ávila": "05",
       "Badajoz": "06", "Balearic Islands": "07", "Barcelona": "08", "Biscay": "48", "Burgos": "09", "Cáceres": "10",
       "Cádiz": "11", "Cantabria": "39", "Castellón": "12", "Ceuta": "51", "Ciudad Real": "13", "Córdoba": "14",
       "Cuenca": "16", "Gipuzkoa": "20", "Girona": "17", "Granada": "18", "Guadalajara": "19", "Huelva": "21",
       "Huesca": "22", "Jaén": "23", "La Rioja": "26", "Las Palmas": "35", "León": "24", "Lleida": "25", "Lugo": "27",
       "Madrid": "28", "Málaga": "29", "Melilla": "52", "Murcia": "30", "Navarre": "31", "Ourense": "32", "Palencia": "34",
       "Pontevedra": "36", "Salamanca": "37", "Santa Cruz de Tenerife": "38", "Segovia": "40", "Seville": "41",
       "Soria": "42", "Tarragona": "43", "Teruel": "44", "Toledo": "45", "Valencia": "46", "Valladolid": "47",
       "Zamora": "49", "Zaragoza": "50"}
CANARIAS = {"35", "38"}
DESPL_CANARIAS = (5.8, 7.2)          # traslado del recuadro de Canarias (grados lon, lat)
ASPECTO = 1 / np.cos(np.radians(40))
ORDEN_PARTIDOS = ["PP", "PSOE", "Vox", "FA", "FV", "Podemos", "ERC", "Junts", "Bildu", "PNV", "BNG", "CCa", "AA", "SALF"]


def _area(anillo):
    x, y = np.asarray(anillo).T
    return 0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _centro(anillo):
    x, y = np.asarray(anillo).T
    c = x * np.roll(y, -1) - np.roll(x, -1) * y
    a = c.sum() / 2
    return (((x + np.roll(x, -1)) * c).sum() / (6 * a), ((y + np.roll(y, -1)) * c).sum() / (6 * a))


def cargar_geo():
    """{código INE: (lista de polígonos [exterior, *huecos], punto donde colocar los escaños)}"""
    from matplotlib.path import Path as MPath  # noqa: F401  (comprobación de dependencia)
    geo = {}
    for f in json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]:
        cod = f["properties"]["cod_prov"]
        polys = []
        for poly in f["geometry"]["coordinates"]:
            anillos = [np.asarray(r, float) for r in poly]
            if cod in CANARIAS:
                anillos = [a + np.array(DESPL_CANARIAS) for a in anillos]
            polys.append(anillos)
        mayor = max(polys, key=lambda p: abs(_area(p[0])))
        geo[cod] = (polys, _centro(mayor[0]))
    return geo


def _dibujar_provincia(ax, polys, color, borde="white", lw=0.7):
    from matplotlib.path import Path as MPath
    from matplotlib.patches import PathPatch
    verts, codes = [], []
    for anillos in polys:
        for k, a in enumerate(anillos):
            # exterior antihorario, huecos horarios: así la regla de relleno respeta los huecos (p. ej. Treviño)
            horario = _area(a) < 0
            if (k == 0 and horario) or (k > 0 and not horario):
                a = a[::-1]
            verts += list(a); codes += [MPath.MOVETO] + [MPath.LINETO] * (len(a) - 2) + [MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color, edgecolor=borde, lw=lw, zorder=1))


def _mezcla(hex_color, t):
    """t = 1 → color puro; t → 0 → blanco."""
    c = np.array(matplotlib.colors.to_rgb(hex_color))
    return tuple(1 - t * (1 - c))


def _marco_mapa(ax):
    x0, y0 = -18.2 + DESPL_CANARIAS[0] - 0.3, 27.5 + DESPL_CANARIAS[1] - 0.25
    ax.plot([x0, -7.2, -7.2, x0, x0], [y0, y0, 29.6 + DESPL_CANARIAS[1], 29.6 + DESPL_CANARIAS[1], y0],
            color=TINTA_3, lw=0.8, zorder=0)
    ax.text(x0 + 0.1, y0 + 0.12, "Canarias", fontsize=9, color=TINTA_2)
    ax.set_xlim(-12.9, 4.6); ax.set_ylim(34.4, 44.0); ax.set_aspect(ASPECTO); ax.axis("off")


def _reparto_tipico(prov):
    """Escaños de cada provincia en el escenario típico calculado en el notebook (§9.3)."""
    cols = [f"tipico_{p}" for p in ORDEN_PARTIDOS if f"tipico_{p}" in prov]
    return {nombre: {c[7:]: int(r[c]) for c in cols if r[c] > 0} for nombre, r in prov.iterrows()}


def mapa_escanos():
    prov = X["provincias"].set_index("provincia")
    geo = cargar_geo()
    reparto = _reparto_tipico(prov)
    fig = plt.figure(figsize=(11, 9.6))
    ax = fig.add_axes([0.0, 0.11, 1.0, 0.70])
    paso_x = 0.165; paso_y = paso_x / ASPECTO
    for nombre, r in prov.iterrows():
        cod = INE[r["prov_wiki"]]
        polys, (cx, cy) = geo[cod]
        _dibujar_provincia(ax, polys, _mezcla(COLORES[r["ganador"]], 0.22))
        asientos = [p for p, n in sorted(reparto[nombre].items(), key=lambda t: -t[1]) for _ in range(n)]
        n = len(asientos)
        if cod in ("51", "52"):                         # Ceuta y Melilla: un punto con etiqueta
            cx, cy = {"51": (-5.32, 35.55), "52": (-2.95, 35.55)}[cod]
            ax.text(cx, cy - 0.22, nombre, ha="center", va="top", fontsize=8.5, color=TINTA_2)
        cols = n if n <= 3 else int(np.ceil(np.sqrt(n) * 1.25))
        filas = int(np.ceil(n / cols))
        for k, p in enumerate(asientos):
            fi, co = divmod(k, cols)
            en_fila = min(cols, n - fi * cols)
            x = cx + (co - (en_fila - 1) / 2) * paso_x
            y = cy + ((filas - 1) / 2 - fi) * paso_y
            ax.scatter(x, y, s=34, color=COLORES[p], edgecolors="white", linewidths=0.7, zorder=3)
    _marco_mapa(ax)

    # barra nacional con los escaños del mapa
    tot = pd.Series({p: sum(r.get(p, 0) for r in reparto.values()) for p in ORDEN_PARTIDOS})
    orden_barra = [p for p in ["Bildu", "BNG", "ERC", "FA", "FV", "Podemos", "AA", "PSOE", "PNV", "Junts", "CCa", "PP", "Vox", "SALF"] if tot[p] > 0]
    bx = fig.add_axes([0.06, 0.035, 0.88, 0.035])
    x = 0
    for p in orden_barra:
        bx.barh(0, tot[p], left=x, color=COLORES[p], edgecolor="white", lw=1.5, height=1)
        if tot[p] >= 25:
            bx.text(x + tot[p] / 2, 0, f"{tot[p]}", ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        x += tot[p]
    bx.plot([175.5, 175.5], [-0.75, 0.75], color=TINTA, lw=1.8, clip_on=False)
    bx.text(175.5, -0.85, "176 = mayoría", ha="center", va="top", fontsize=9.5, color=TINTA)
    bx.set_xlim(0, 350); bx.set_ylim(-0.5, 0.5); bx.axis("off")
    orden_ley = sorted(orden_barra, key=lambda p: -tot[p])
    for k, p in enumerate(orden_ley):
        fx, fy = 0.06 + (k % 6) * 0.155, -0.005 - (k // 6) * 0.028
        fig.text(fx, fy, "●", color=COLORES[p], fontsize=11, va="center")
        fig.text(fx + 0.017, fy, f"{NOMBRE.get(p, p)} {tot[p]}", color=TINTA, fontsize=9.5, va="center")

    pv = bloques.loc["PP + Vox", "probabilidad"]; inv = bloques.loc["Bloque investidura 2023 con Junts", "probabilidad"]
    titulo(fig, "Dónde se ganan los escaños",
           "Un punto por escaño en el escenario típico · fondo: partido más votado en la provincia", y=0.985)
    for fx, valor, texto in [(0.0, pv, "probabilidad de que PP + Vox\nsumen 176 escaños"),
                             (0.26, inv, "probabilidad de que lo sumen los\nsocios de la investidura de 2023")]:
        fig.add_artist(plt.Line2D([fx, fx + 0.2], [0.925, 0.925], color=TINTA, lw=2.5))
        fig.text(fx, 0.915, pct(valor), fontsize=26, fontweight="bold", color=TINTA, va="top")
        fig.text(fx, 0.862, texto, fontsize=10, color=TINTA_2, va="top")
    fig.text(0.0, -0.075, "Escenario típico: de 8.000 simulaciones, la de total nacional más cercano a la mediana y más parecida "
             "a la media de cada provincia.", fontsize=8.5, color=TINTA_3)
    guardar(fig, "mapa_escanos.png")


def mapa_ganador():
    prov = X["provincias"].set_index("provincia")
    geo = cargar_geo()
    cortes = [(0.0, 0.6, 0.28, "menos del 60 %"), (0.6, 0.8, 0.5, "60–80 %"), (0.8, 0.95, 0.75, "80–95 %"), (0.95, 1.01, 1.0, "95 % o más")]
    fig, ax = plt.subplots(figsize=(11, 8.2))
    for nombre, r in prov.iterrows():
        cod = INE[r["prov_wiki"]]
        t = next(t for a, b, t, _ in cortes if a <= r["P_ganador"] < b)
        polys, (cx, cy) = geo[cod]
        _dibujar_provincia(ax, polys, _mezcla(COLORES[r["ganador"]], t))
        if cod in ("51", "52"):
            cx, cy = {"51": (-5.32, 35.55), "52": (-2.95, 35.55)}[cod]
            ax.scatter(cx, cy, s=110, color=_mezcla(COLORES[r["ganador"]], t), edgecolors=TINTA_3, lw=0.8, zorder=3)
            ax.text(cx, cy - 0.2, nombre, ha="center", va="top", fontsize=8.5, color=TINTA_2)
    # etiquetas de las provincias en disputa
    for nombre, r in prov[prov.P_ganador < 0.6].iterrows():
        cod = INE[r["prov_wiki"]]
        if cod in ("51", "52"):
            continue
        cx, cy = geo[cod][1]
        ax.text(cx, cy, f"{nombre}\n{NOMBRE.get(r['ganador'], r['ganador'])} {r['P_ganador']:.0%}".replace("%", " %"),
                ha="center", va="center", fontsize=7.8, color=TINTA, zorder=4, linespacing=1.1)
    _marco_mapa(ax)

    # leyenda: partidos y seguridad
    ganadores = [p for p in ORDEN_PARTIDOS if p in set(prov.ganador)]
    lx = fig.add_axes([0.06, 0.02, 0.88, 0.07]); lx.axis("off"); lx.set_xlim(0, 1); lx.set_ylim(0, 1)
    x = 0.0
    for p in ganadores:
        n = int((prov.ganador == p).sum())
        lx.add_patch(plt.Rectangle((x, 0.62), 0.025, 0.3, color=COLORES[p]))
        lx.text(x + 0.032, 0.77, f"{NOMBRE.get(p, p)}  ({n} {'provincia' if n == 1 else 'provincias'})", va="center",
                fontsize=10.5, color=TINTA)
        x += 0.26
    lx.text(0.0, 0.18, "El partido gana en el … de las simulaciones:", va="center", fontsize=10.5, color=TINTA_2)
    x = 0.38
    for _, _, t, etiqueta in cortes:
        lx.add_patch(plt.Rectangle((x, 0.04), 0.025, 0.3, color=_mezcla("#57606a", t)))
        lx.text(x + 0.032, 0.18, etiqueta, va="center", fontsize=10, color=TINTA)
        x += 0.15
    titulo(fig, "¿Quién gana en cada provincia, y con qué seguridad?",
           "Partido más votado en cada provincia. Color pálido: provincia en disputa, el ganador cambia de unas simulaciones a otras",
           y=0.99)
    guardar(fig, "mapa_ganador.png")


if __name__ == "__main__":
    print("Generando figuras en", IMG)
    hemiciclo(); probabilidades(); rangos(); sesgo_encuestadoras(); y_si_fallan(); prueba_2023(); tendencia_desde_notebook()
    if "provincias" in X and GEOJSON.exists():
        mapa_escanos(); mapa_ganador()
    else:
        print("  ! Falta la hoja «provincias» del Excel o data/provincias_espana.geojson: se omiten los mapas")

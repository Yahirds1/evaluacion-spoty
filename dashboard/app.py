"""
Dashboard: Segmentación de canciones de Spotify con K-Means.
Ejecutar desde la raíz del proyecto:  streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
AUDIO = ["danceability", "energy", "acousticness", "valence"]

# Paleta: luz de lámpara, madera, plantas y ciruela
AMBAR, VERDE, CREMA = "#e8a33d", "#7fa36a", "#f3e6d3"
COLORES = {
    "Bailable y alegre": AMBAR,
    "Intenso y enérgico": "#c4472f",
    "Acústico relajado": VERDE,
    "Íntimo y melancólico": "#a874a8",
}

st.set_page_config(page_title="Segmentación musical con K-Means", page_icon="🎧", layout="wide")

# ------------------------------------------------- Plantilla de las gráficas
pio.templates["rnb"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=CREMA, family="DM Sans, sans-serif"),
    title=dict(font=dict(family="Playfair Display, Georgia, serif", size=19)),
    colorway=[AMBAR, VERDE, "#c4472f", "#a874a8"],
    xaxis=dict(gridcolor="rgba(243,230,211,.10)", zerolinecolor="rgba(243,230,211,.20)"),
    yaxis=dict(gridcolor="rgba(243,230,211,.10)", zerolinecolor="rgba(243,230,211,.20)"),
))
px.defaults.template = "rnb"
px.defaults.color_continuous_scale = ["#3b1f2b", "#c4472f", AMBAR, CREMA]
DIVERGENTE = [[0, "#c4472f"], [0.5, "#3a2418"], [1, VERDE]]

# -------------------------------------------------------------- Estilo (CSS)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@600;700&display=swap');

.stApp{
  background:
    radial-gradient(800px 460px at 88% -6%, rgba(255,184,77,.24), transparent 62%),
    radial-gradient(600px 400px at -5% 105%, rgba(127,163,106,.12), transparent 60%),
    #1a110c;
}
html, body, [class*="css"]{font-family:'DM Sans',sans-serif;}
h1,h2,h3{font-family:'Playfair Display',Georgia,serif !important;letter-spacing:.2px;}
h3{border-bottom:1px solid rgba(232,163,61,.35);padding-bottom:6px;margin-top:1.6rem !important;}

/* Barra lateral: madera oscura */
[data-testid="stSidebar"]{
  background:repeating-linear-gradient(92deg,#2b1a11 0 7px,#26170f 7px 13px,#2e1d13 13px 18px);
  border-right:2px solid #4a2f1b;
}
[data-testid="stSidebar"] h2{color:#e8a33d;}

/* Tarjetas de indicadores */
[data-testid="stMetric"]{
  background:linear-gradient(160deg,rgba(60,38,24,.85),rgba(38,23,15,.85));
  border:1px solid rgba(232,163,61,.28);
  border-radius:14px;padding:14px 18px;
  box-shadow:0 0 22px rgba(232,163,61,.10), inset 0 1px 0 rgba(255,255,255,.05);
}
[data-testid="stMetricValue"]{font-family:'Playfair Display',serif;color:#ffd08a;}
[data-testid="stMetricLabel"]{color:#c9b79c;}

/* Cabecera con tornamesa */
.hero{
  position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;
  gap:24px;flex-wrap:wrap;padding:34px 40px 34px 150px;margin-bottom:22px;border-radius:20px;
  border:1px solid rgba(232,163,61,.30);
  background:
    radial-gradient(500px 260px at 100% 0%, rgba(255,184,77,.22), transparent 65%),
    linear-gradient(135deg,#3a2316,#241610);
  box-shadow:0 18px 40px rgba(0,0,0,.45);
}
.hero h1{margin:0 0 6px;font-size:clamp(1.7rem,4vw,2.5rem);line-height:1.1;color:#fff1da;}
.hero .eyebrow{margin:0 0 8px;color:#e8a33d;text-transform:uppercase;letter-spacing:3px;font-size:.78rem;font-weight:700;}
.hero .sub{margin:0;color:#d9c7ac;max-width:46ch;}
.leaves{position:absolute;left:0;top:0;width:150px;height:170px;pointer-events:none;}

/* Ecualizador */
.eq{display:flex;align-items:flex-end;gap:4px;height:26px;margin-top:16px;}
.eq span{width:5px;border-radius:2px;background:#e8a33d;animation:bounce 1.1s ease-in-out infinite;}
.eq span:nth-child(1){height:40%;animation-delay:-.9s}
.eq span:nth-child(2){height:90%;animation-delay:-.6s}
.eq span:nth-child(3){height:60%;animation-delay:-.3s}
.eq span:nth-child(4){height:100%;animation-delay:-.75s}
.eq span:nth-child(5){height:50%;animation-delay:-.15s}
.eq em{margin-left:10px;font-style:normal;color:#c9b79c;font-size:.85rem;align-self:center;}
@keyframes bounce{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}

/* Tornamesa y disco */
.deck{
  position:relative;padding:18px;border-radius:16px;
  background:repeating-linear-gradient(92deg,#6a4426 0 6px,#5a3a20 6px 11px,#70492a 11px 15px);
  box-shadow:0 12px 26px rgba(0,0,0,.55), inset 0 0 0 2px rgba(0,0,0,.25);
}
.record{position:relative;width:170px;height:170px;}
.vinyl{
  position:absolute;inset:0;border-radius:50%;
  background:
    radial-gradient(circle,#1a110c 0 2.5%,#e8a33d 2.5% 13%,#8c5a1c 13% 15%,transparent 15%),
    repeating-radial-gradient(circle,#0c0807 0 2px,#1b1311 3px 4px);
  animation:spin 5s linear infinite;
  box-shadow:0 8px 22px rgba(0,0,0,.65);
}
.sheen{
  position:absolute;inset:0;border-radius:50%;pointer-events:none;
  background:conic-gradient(from 30deg,transparent 0 8%,rgba(255,255,255,.13) 14%,transparent 24%,transparent 55%,rgba(255,255,255,.10) 64%,transparent 74%);
}
.pivot{position:absolute;right:10px;top:8px;width:20px;height:20px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%,#e8d9b8,#8f7b57);box-shadow:0 2px 6px rgba(0,0,0,.6);}
.arm{
  position:absolute;right:19px;top:16px;width:5px;height:118px;border-radius:3px;
  background:linear-gradient(#e0cfae,#9c8a68);transform-origin:50% 0;transform:rotate(24deg);
  box-shadow:0 2px 5px rgba(0,0,0,.5);animation:drop 2.4s ease-out 1;
}
.arm::after{content:"";position:absolute;left:-4px;bottom:-9px;width:13px;height:14px;border-radius:2px;background:#c8b48c;}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes drop{from{transform:rotate(-8deg)}to{transform:rotate(24deg)}}

@media (max-width:760px){.hero{padding:120px 22px 26px}}
@media (prefers-reduced-motion:reduce){.vinyl,.eq span,.arm{animation:none !important}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def cargar():
    return pd.read_csv(RAIZ / "data" / "procesado.csv")


df = cargar()

# ------------------------------------------------------------------ Filtros
st.sidebar.header("🎚️ Filtros")
generos = st.sidebar.multiselect("Género musical", sorted(df["track_genre"].unique()))
pop_min, pop_max = st.sidebar.slider("Popularidad", 0, 100, (0, 100))
explicito = st.sidebar.selectbox("Contenido explícito", ["Todos", "Solo explícitas", "Sin contenido explícito"])
pagina = st.sidebar.radio("Página", ["1. Análisis general", "2. Segmentación K-Means"])

f = df[df["popularity"].between(pop_min, pop_max)]
if generos:
    f = f[f["track_genre"].isin(generos)]
if explicito == "Solo explícitas":
    f = f[f["explicit"] == 1]
elif explicito == "Sin contenido explícito":
    f = f[f["explicit"] == 0]

# ------------------------------------------------------------------ Cabecera
st.markdown(f"""
<div class="hero">
  <svg class="leaves" viewBox="0 0 150 170" aria-hidden="true">
    <path d="M18 0 C 22 50, 40 80, 70 120" stroke="#4d6b41" stroke-width="3" fill="none"/>
    <g fill="#5f8a55">
      <path d="M26 40 C 60 20, 95 34, 104 64 C 70 76, 38 66, 26 40Z"/>
      <path d="M44 84 C 80 70, 112 86, 118 116 C 82 124, 52 112, 44 84Z" fill="#6f9a62"/>
      <path d="M14 22 C -6 40, -4 72, 20 84 C 34 62, 30 38, 14 22Z" fill="#4d7a47"/>
      <path d="M62 118 C 78 126, 96 146, 94 168 C 70 160, 58 140, 62 118Z" fill="#587f4e"/>
    </g>
    <path d="M26 40 C 50 44, 80 50, 104 64" stroke="#3b5c35" stroke-width="1.5" fill="none"/>
  </svg>
  <div>
    <p class="eyebrow">Spotify · K-Means</p>
    <h1>Segmentación de canciones de Spotify</h1>
    <p class="sub">Cuatro maneras de sentir una canción, según su energía, su ánimo y su sonido.</p>
    <div class="eq"><span></span><span></span><span></span><span></span><span></span>
      <em>Ahora suenan {len(f):,} canciones</em></div>
  </div>
  <div class="deck">
    <div class="record"><div class="vinyl"></div><div class="sheen"></div></div>
    <div class="pivot"></div><div class="arm"></div>
  </div>
</div>
""", unsafe_allow_html=True)

if f.empty:
    st.warning("Los filtros no devuelven canciones. Amplía la selección.")
    st.stop()

# --------------------------------------------------------------------- KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Canciones", f"{len(f):,}")
c2.metric("Popularidad promedio", f"{f['popularity'].mean():.1f}")
c3.metric("Duración promedio", f"{f['duration_min'].mean():.2f} min")
c4.metric("Canciones explícitas", f"{f['explicit'].mean() * 100:.1f}%")

# ======================================================= PÁGINA 1: GENERAL
if pagina.startswith("1"):
    st.subheader("Análisis general del dataset")
    a, b = st.columns(2)
    a.plotly_chart(
        px.histogram(f, x="popularity", nbins=30, title="Distribución de la popularidad",
                     labels={"popularity": "Popularidad"}, color_discrete_sequence=[AMBAR]),
        width="stretch")
    top = f["track_genre"].value_counts().head(10).reset_index()
    top.columns = ["Género", "Canciones"]
    b.plotly_chart(
        px.bar(top, x="Canciones", y="Género", orientation="h", title="Géneros con más canciones",
               color_discrete_sequence=[VERDE]).update_yaxes(autorange="reversed"),
        width="stretch")

    a, b = st.columns(2)
    corr = f[AUDIO + ["loudness", "tempo", "popularity"]].corr().round(2)
    a.plotly_chart(px.imshow(corr, text_auto=True, color_continuous_scale=DIVERGENTE, zmin=-1, zmax=1,
                             title="Correlación entre variables"), width="stretch")
    b.plotly_chart(
        px.scatter(f.sample(min(4000, len(f)), random_state=1), x="energy", y="acousticness",
                   color="popularity", title="Energía vs. acústica", opacity=0.6,
                   labels={"energy": "Energía", "acousticness": "Acústica"}),
        width="stretch")

    st.subheader("Estadísticas descriptivas")
    st.dataframe(f[["popularity", "duration_min"] + AUDIO + ["loudness", "tempo"]].describe().T.round(2),
                 width="stretch")

# ===================================================== PÁGINA 2: K-MEANS
else:
    st.subheader("Segmentación mediante K-Means (K = 4)")
    st.caption("Variables usadas: danceability, energy, loudness, acousticness, valence y tempo, "
               "escaladas con StandardScaler.")

    orden = list(COLORES)
    a, b = st.columns([1, 2])
    dist = f["cluster_nombre"].value_counts().reset_index()
    dist.columns = ["Grupo", "Canciones"]
    a.plotly_chart(px.bar(dist, x="Grupo", y="Canciones", color="Grupo", color_discrete_map=COLORES,
                          title="Canciones por clúster").update_layout(showlegend=False),
                   width="stretch")
    b.plotly_chart(
        px.scatter(f.sample(min(8000, len(f)), random_state=1), x="pca1", y="pca2",
                   color="cluster_nombre", color_discrete_map=COLORES, opacity=0.6,
                   hover_data=["track_name", "artists", "track_genre"],
                   title="Agrupamientos (PCA a 2 dimensiones)",
                   labels={"pca1": "Componente 1", "pca2": "Componente 2", "cluster_nombre": "Grupo"}),
        width="stretch")

    medias = f.groupby("cluster_nombre")[AUDIO].mean().reset_index().melt(
        id_vars="cluster_nombre", var_name="Característica", value_name="Promedio")
    a, b = st.columns(2)
    a.plotly_chart(
        px.bar(medias, x="Característica", y="Promedio", color="cluster_nombre", barmode="group",
               color_discrete_map=COLORES, title="Perfil de audio por clúster",
               labels={"cluster_nombre": "Grupo"}),
        width="stretch")
    b.plotly_chart(
        px.box(f, x="cluster_nombre", y="popularity", color="cluster_nombre", color_discrete_map=COLORES,
               category_orders={"cluster_nombre": orden}, title="Popularidad por clúster",
               labels={"cluster_nombre": "Grupo", "popularity": "Popularidad"}).update_layout(showlegend=False),
        width="stretch")

    st.subheader("Estadísticas descriptivas por clúster")
    tabla = f.groupby("cluster_nombre").agg(
        Canciones=("track_id", "count"), Popularidad=("popularity", "mean"),
        Duracion_min=("duration_min", "mean"), Bailabilidad=("danceability", "mean"),
        Energia=("energy", "mean"), Acustica=("acousticness", "mean"),
        Valencia=("valence", "mean"), Tempo=("tempo", "mean"), Volumen_dB=("loudness", "mean")).round(2)
    st.dataframe(tabla, width="stretch")

    st.subheader("Descripción de los grupos")
    st.markdown("""
- **Bailable y alegre:** alta bailabilidad (0.70), energía media-alta y la mayor valencia (0.70). Música positiva para fiestas. Es el grupo más grande.
- **Intenso y enérgico:** la mayor energía (0.82), el tempo más rápido (137 BPM) y casi nada de acústica. Predominan géneros como metal y grindcore.
- **Acústico relajado:** energía baja-media (0.43) y acústica alta (0.65), de ánimo neutro. Géneros como tango y honky-tonk.
- **Íntimo y melancólico:** el grupo más pequeño, con muy baja energía (0.17), muy acústico (0.86) y la valencia más baja. Incluye new-age, ambient y música para dormir.
""")

    st.subheader("Hallazgos y recomendaciones")
    h, r = st.columns(2)
    h.markdown("""
**Hallazgos**
1. Los cuatro grupos se distinguen sobre todo por energía y acústica.
2. La popularidad es casi igual en tres grupos (unos 34 puntos); solo el grupo íntimo y melancólico baja a 28.
3. Casi no hay contenido explícito en el grupo íntimo (1%), frente a 10-11% en los grupos de más energía.
""")
    r.markdown("""
**Recomendaciones**
1. Armar listas por estado de ánimo usando estos grupos (fiesta, entrenamiento, relajación, dormir).
2. Recomendar canciones del mismo clúster que las que el usuario ya escucha.
3. Para promocionar música del grupo íntimo, enfocarse en momentos de descanso, ya que tiene menos popularidad general.
""")

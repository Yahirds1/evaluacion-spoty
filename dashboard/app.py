"""
Dashboard: Segmentación de canciones de Spotify con K-Means.
Ejecutar desde la raíz del proyecto:  streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
AUDIO = ["danceability", "energy", "acousticness", "valence"]
COLORES = {
    "Bailable y alegre": "#1db954",
    "Intenso y enérgico": "#e8590c",
    "Acústico relajado": "#4dabf7",
    "Íntimo y melancólico": "#9775fa",
}

st.set_page_config(page_title="Segmentación musical con K-Means", page_icon="🎧", layout="wide")


@st.cache_data
def cargar():
    return pd.read_csv(RAIZ / "data" / "procesado.csv")


df = cargar()

# ------------------------------------------------------------------ Filtros
st.sidebar.header("Filtros")
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

st.title("🎧 Segmentación de canciones de Spotify con K-Means")

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
                     labels={"popularity": "Popularidad"}, color_discrete_sequence=["#1db954"]),
        width="stretch")
    top = f["track_genre"].value_counts().head(10).reset_index()
    top.columns = ["Género", "Canciones"]
    b.plotly_chart(
        px.bar(top, x="Canciones", y="Género", orientation="h", title="Géneros con más canciones",
               color_discrete_sequence=["#1db954"]).update_yaxes(autorange="reversed"),
        width="stretch")

    a, b = st.columns(2)
    corr = f[AUDIO + ["loudness", "tempo", "popularity"]].corr().round(2)
    a.plotly_chart(px.imshow(corr, text_auto=True, color_continuous_scale="RdYlGn", zmin=-1, zmax=1,
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

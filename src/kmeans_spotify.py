"""
Segmentación de canciones de Spotify con K-Means.
Ejecutar desde la raíz del proyecto:  python src/kmeans_spotify.py
Genera: data/procesado.csv, data/metricas.json e imágenes en images/
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parent.parent
DATOS, IMG = RAIZ / "data", RAIZ / "images"
IMG.mkdir(exist_ok=True)

VARIABLES = ["danceability", "energy", "loudness", "acousticness", "valence", "tempo"]
K_FINAL = 4
K_COMPARAR = 3


# ---------------------------------------------------------------- 1. Carga
df = pd.read_csv(DATOS / "original.csv", index_col=0)
print("Primeros 10 registros:\n", df.head(10))
print("\nDimensiones:", df.shape)
print("\nTipos de datos:\n", df.dtypes)
print("\nEstadísticas descriptivas:\n", df.describe().T)
print("\nValores nulos:\n", df.isna().sum()[df.isna().sum() > 0])
print("\nFilas duplicadas:", df.duplicated().sum())
print("track_id repetidos:", df["track_id"].duplicated().sum())

# ----------------------------------------------- 2. Gráficas exploratorias
sns.set_theme(style="whitegrid")

plt.figure(figsize=(8, 4))
sns.histplot(df["popularity"], bins=30, color="#1db954")
plt.title("Distribución de la popularidad")
plt.tight_layout()
plt.savefig(IMG / "eda_popularidad.png", dpi=120)
plt.close()

plt.figure(figsize=(8, 6))
sns.heatmap(df[VARIABLES + ["popularity"]].corr(), annot=True, fmt=".2f", cmap="RdYlGn", center=0)
plt.title("Correlación entre variables de audio")
plt.tight_layout()
plt.savefig(IMG / "eda_correlacion.png", dpi=120)
plt.close()

plt.figure(figsize=(9, 4))
df["track_genre"].value_counts().head(10).plot(kind="bar", color="#1db954")
plt.title("Géneros con más canciones")
plt.ylabel("Canciones")
plt.tight_layout()
plt.savefig(IMG / "eda_generos.png", dpi=120)
plt.close()

# ----------------------------------------------------------- 3. Limpieza
n0 = len(df)
df = df.dropna(subset=["artists", "album_name", "track_name"])
df = df.drop_duplicates()
# Una misma canción aparece en varios géneros: se conserva la fila más popular
df = df.sort_values("popularity", ascending=False).drop_duplicates("track_id")
# Valores imposibles o atípicos
df = df[(df["tempo"] > 0) & df["duration_ms"].between(30_000, 900_000)]
df["explicit"] = df["explicit"].astype(int)
df["duration_min"] = (df["duration_ms"] / 60000).round(2)
df = df.reset_index(drop=True)
print(f"\nLimpieza: {n0} -> {len(df)} registros")

# -------------------------------------------------------- 4. Escalamiento
escalador = StandardScaler()
X = escalador.fit_transform(df[VARIABLES])

# ----------------------------------------------- 5. Evaluar valores de K
resultados = []
for k in range(2, 9):
    m = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    sil = silhouette_score(X, m.labels_, sample_size=10_000, random_state=42)
    resultados.append({"k": k, "inercia": m.inertia_, "silhouette": sil})
    print(f"K={k}  inercia={m.inertia_:,.0f}  silhouette={sil:.3f}")
res = pd.DataFrame(resultados)

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(res["k"], res["inercia"], marker="o", color="#1db954")
ax[0].set(title="Método del codo", xlabel="K", ylabel="Inercia")
ax[1].plot(res["k"], res["silhouette"], marker="o", color="#e8590c")
ax[1].set(title="Coeficiente de silueta", xlabel="K", ylabel="Silhouette")
plt.tight_layout()
plt.savefig(IMG / "evaluacion_k.png", dpi=120)
plt.close()

# ---------------------------------------------------------- 6. Modelo final
modelo = KMeans(n_clusters=K_FINAL, random_state=42, n_init=10)
df["cluster"] = modelo.fit_predict(X)
centroides = pd.DataFrame(escalador.inverse_transform(modelo.cluster_centers_), columns=VARIABLES)
print("\nCentroides (unidades originales):\n", centroides.round(3))
print("\nRegistros por clúster:\n", df["cluster"].value_counts().sort_index())

# Nombres según los centroides (así no dependen del número que asigne KMeans)
NOMBRES = {}
NOMBRES[int(centroides["energy"].idxmin())] = "Íntimo y melancólico"
resto = centroides.drop(index=list(NOMBRES))
NOMBRES[int(resto["valence"].idxmax())] = "Bailable y alegre"
resto = centroides.drop(index=list(NOMBRES))
NOMBRES[int(resto["energy"].idxmax())] = "Intenso y enérgico"
NOMBRES[int(centroides.drop(index=list(NOMBRES)).index[0])] = "Acústico relajado"
print("\nNombres:", NOMBRES)

# Comparación con otra configuración
alt = KMeans(n_clusters=K_COMPARAR, random_state=42, n_init=10).fit(X)
comparacion = {
    f"K={K_COMPARAR}": {
        "silhouette": float(silhouette_score(X, alt.labels_, sample_size=10_000, random_state=42)),
        "tamanos": pd.Series(alt.labels_).value_counts().sort_index().tolist(),
    },
    f"K={K_FINAL}": {
        "silhouette": float(silhouette_score(X, modelo.labels_, sample_size=10_000, random_state=42)),
        "tamanos": df["cluster"].value_counts().sort_index().tolist(),
    },
}
print("\nComparación:", comparacion)

# Gráfica de agrupamientos (PCA a 2 dimensiones)
pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(X)
df["pca1"], df["pca2"] = coords[:, 0], coords[:, 1]
muestra = df.sample(8000, random_state=42)
plt.figure(figsize=(9, 6))
sns.scatterplot(data=muestra, x="pca1", y="pca2", hue="cluster", palette="Set2", s=12, alpha=0.6)
cc = pca.transform(modelo.cluster_centers_)
plt.scatter(cc[:, 0], cc[:, 1], color="red", marker="X", s=250, label="Centroides")
plt.title("Clústeres de canciones (PCA)")
plt.legend()
plt.tight_layout()
plt.savefig(IMG / "clusters_pca.png", dpi=120)
plt.close()

# ------------------------------------------------------------ 7. Exportar
df["cluster_nombre"] = df["cluster"].map(NOMBRES)
df.to_csv(DATOS / "procesado.csv", index=False)
with open(DATOS / "metricas.json", "w", encoding="utf-8") as f:
    json.dump({
        "variables": VARIABLES,
        "k_final": K_FINAL,
        "evaluacion_k": res.to_dict("records"),
        "comparacion": comparacion,
        "varianza_pca": [float(v) for v in pca.explained_variance_ratio_],
        "registros_original": int(n0),
        "registros_limpios": int(len(df)),
        "centroides": centroides.round(4).to_dict("records"),
    }, f, indent=2, ensure_ascii=False)
print("\nListo: data/procesado.csv y data/metricas.json generados.")

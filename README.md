# Segmentación de canciones de Spotify con K-Means

Proyecto integrador de minería de datos: se agrupan canciones según sus características de audio con el algoritmo K-Means y se presentan los resultados en un dashboard interactivo hecho con Streamlit.

## Descripción

- **Problema:** identificar tipos de canciones con características parecidas (energía, ritmo, ánimo) para poder armar listas y recomendaciones.
- **Dataset:** Spotify Tracks, 114,000 registros y 20 variables.
  Fuente: https://raw.githubusercontent.com/RitvikChouhan/Spotify_Analysis/main/spotify_tracks.csv
- **Variables del modelo:** danceability, energy, loudness, acousticness, valence y tempo.
- **Resultado:** 4 clústeres (K = 4): Bailable y alegre, Intenso y enérgico, Acústico relajado, Íntimo y melancólico.

## Herramientas

Python, pandas, scikit-learn, matplotlib, seaborn, plotly y Streamlit.

## Estructura del repositorio

```
├── README.md
├── requirements.txt
├── data/
│   ├── original.csv      Dataset original
│   ├── procesado.csv     Dataset limpio con el clúster asignado
│   └── metricas.json     Métricas y centroides del modelo
├── src/
│   └── kmeans_spotify.py Exploración, limpieza, K-Means y exportación
├── dashboard/
│   └── app.py            Dashboard en Streamlit (2 páginas)
├── images/               Gráficas generadas por el script
└── docs/
    └── documentacion.pdf Documento del proyecto
```

## Cómo ejecutarlo

1. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Ejecutar el análisis (genera `data/procesado.csv` y las imágenes):
   ```
   python src/kmeans_spotify.py
   ```
3. Abrir el dashboard:
   ```
   streamlit run dashboard/app.py
   ```
   Se abre en el navegador, normalmente en http://localhost:8501.

## Dashboard

- **Página 1, Análisis general:** 4 indicadores, distribución de popularidad, géneros principales, correlaciones y estadísticas.
- **Página 2, Segmentación K-Means:** canciones por clúster, gráfica de dispersión (PCA), perfil de audio y popularidad por grupo, tabla de estadísticas, descripción de grupos, hallazgos y recomendaciones.
- **Filtros:** género, rango de popularidad y contenido explícito.

## Limpieza realizada

De 114,000 registros quedaron 89,432: se eliminó 1 fila con nulos de texto, 450 duplicados exactos, 23,809 canciones repetidas por aparecer en varios géneros (se conservó la más popular), 157 con tempo igual a 0 y 155 con duración fuera del rango de 30 segundos a 15 minutos (algunas cumplían ambas condiciones). Después se aplicó `StandardScaler`.

## Elección de K

Se evaluaron K de 2 a 8 con el método del codo y el coeficiente de silueta. La silueta es mayor con K = 2 (0.327), pero solo separa música tranquila de música intensa. Con K = 4 (silueta 0.217) los grupos son más específicos e interpretables, por lo que se eligió K = 4. Se comparó también con K = 3 (silueta 0.230).

## Limitaciones

- La silueta es moderada (0.2 a 0.3): los grupos se traslapan y no tienen fronteras claras.
- K-Means solo usa distancias en variables numéricas; no considera género ni artista.
- Se conservó una sola fila por canción, por lo que se pierde que algunas canciones pertenecen a varios géneros.

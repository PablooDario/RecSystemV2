# Sistema de Recomendacion de Peliculas Hibrido

Sistema de recomendacion de peliculas que combina cuatro modelos para generar recomendaciones personalizadas, incluyendo un enfoque basado en personalidad (Big Five) que permite resolver el problema de cold-start.

## Arquitectura

```
frontend/ (React + Vite)
    └── Interfaz de usuario
backend/ (FastAPI + SQLAlchemy)
    └── API REST → Motor de Recomendaciones → Modelos
ml/ (NumPy, scikit-surprise)
    └── Notebooks de entrenamiento y evaluacion
database/ (MySQL)
    └── Schema + Seeds
```

## Modelos de Recomendacion

| Modelo | Activacion | Descripcion |
|--------|-----------|-------------|
| Personalidad (PMLP) | 0 ratings | MLP que mapea Big Five → embeddings de items (cold-start) |
| Content-Based | 1+ ratings positivos | Similitud coseno ponderada por campo (overview, genres, cast, etc.) |
| Collaborative Filtering (LightGCN) | 10+ ratings | Embeddings colaborativos aprendidos con BPR |
| Hibrido (Weighted Score Fusion) | 15+ ratings | Combinacion ponderada de los 4 modelos |

## Requisitos

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

## Instalacion

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd Final\ RS
```

### 2. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crear archivo `backend/.env`:

```env
DB_USER=root
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=recommendation_system
```

### 3. Base de datos

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p recommendation_system < database/seed_movies_benchmark.sql
mysql -u root -p recommendation_system < database/seed_actors_benchmark.sql
mysql -u root -p recommendation_system < database/seed_movie_actors_benchmark.sql
```

### 4. Archivos de modelos (no incluidos en el repo por tamanio)

Los siguientes archivos deben generarse localmente:

| Archivo | Como generarlo |
|---------|---------------|
| `ml/data/benchmark/cosine_sim_benchmark.npy` | `python -m ml.scripts.build_content_similarity` |
| `ml/models/saved/lightgcn_benchmark.npz` | Ejecutar notebook 13 |
| `ml/models/saved/pmlp_sv.pkl` | Ejecutar notebook 13 |
| `ml/data/raw/ratings.parquet` | Descargar de [MovieLens 32M](https://grouplens.org/datasets/movielens/) |

### 5. Frontend

```bash
cd frontend
npm install
```

## Ejecucion

### Backend
```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

## Estructura del Proyecto

```
.
├── backend/
│   ├── app/
│   │   ├── core/           # Configuracion (DB connection)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/
│   │       └── recommendations/
│   │           ├── engine.py              # Motor principal
│   │           ├── model_loader.py        # Carga lazy de artefactos
│   │           ├── personality_recommender.py
│   │           ├── content_based.py
│   │           ├── cf_recommender.py
│   │           └── hybrid_recommender.py
│   └── main.py
├── frontend/
│   └── src/
│       ├── components/     # React components
│       └── services/       # API clients
├── ml/
│   ├── config.py           # Paths y utilidades
│   ├── data/
│   │   ├── raw/            # Datos crudos (MovieLens 32M)
│   │   ├── processed/      # Datos intermedios (5k peliculas)
│   │   ├── benchmark/      # Dataset final (3,830 peliculas)
│   │   └── DataNewUsers/   # Datos de usuarios del survey
│   ├── evaluation/         # Metricas y splits
│   ├── models/             # Implementaciones de modelos
│   ├── notebooks/          # Pipeline completo (1-15)
│   └── scripts/            # Scripts standalone
├── database/
│   ├── schema.sql
│   ├── create_benchmark_seed.py
│   └── seed_*_benchmark.sql
└── requirements.txt
```

## Pipeline de Notebooks

| # | Notebook | Funcion |
|---|----------|---------|
| 1 | Fetch_Movies_Details | Descarga metadatos de TMDB (5,000 peliculas) |
| 2 | Movies_EDA | Analisis exploratorio |
| 3 | Cleaning_and_Filtering | Limpieza del catalogo |
| 4 | Fetch_Crew_and_Keywords | Descarga crew y keywords de TMDB |
| 5 | Filtering_Ratings | Filtrado de ratings crudos |
| 6 | Extracting_Personality | Derivacion de Big Five via Nave et al. |
| 7 | Fetch_Spanish_Details | Traduccion de metadatos al espaniol |
| 8 | Build_Benchmark_Dataset | Construccion del dataset final (3,830 peliculas, 6,000 usuarios) |
| 9 | Fetch_Actors_Poster | Descarga actores de TMDB + generacion SQL |
| 10 | Popularity_Baseline | Modelo baseline de popularidad |
| 11 | Content_Based | Modelo basado en contenido |
| 12 | Collaborative_Filtering | LightGCN, SVD, BPR-MF |
| 13 | Personality_Cross_Eval | PMLP con evaluacion cruzada Benchmark/Survey |
| 14 | Hybrid_Model | Weighted Score Fusion |
| 15 | Model_Comparison | Comparacion final de todos los modelos |

## Dataset Benchmark

Construido a partir de MovieLens 32M, disenado para aproximar las dimensiones de ML-1M:

| Metrica | ML-1M (referencia) | Este dataset |
|---------|-------------------|--------------|
| Ratings | 1,000,209 | 1,000,279 |
| Usuarios | 6,040 | 6,000 |
| Items | 3,882 | 3,830 |
| Densidad | 4.27% | 4.35% |

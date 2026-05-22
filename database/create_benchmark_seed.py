"""
Generate the SQL seed file for the benchmark movies table.

Reads movies_benchmark_spanish.csv (3,830 movies with Spanish metadata)
and produces seed_movies_benchmark.sql ready for MySQL import.

Usage:
    python create_benchmark_seed.py
"""
import ast
import json
from pathlib import Path

import pandas as pd

_DB_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _DB_DIR.parent

_SPANISH_BENCH_CSV = _PROJECT_DIR / "ml" / "data" / "benchmark" / "movies_benchmark_spanish.csv"


def esc(value) -> str:
    if pd.isna(value) or value == "":
        return ""
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def to_json_genres(value) -> str:
    if isinstance(value, str) and value.startswith("["):
        try:
            parsed = ast.literal_eval(value)
            if parsed and isinstance(parsed[0], dict):
                names = [g["name"] for g in parsed]
                return json.dumps(names, ensure_ascii=False)
            return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            return json.dumps([])
    return json.dumps([])


def sql_value(val, is_string: bool = False) -> str:
    if pd.isna(val) or val == "":
        return "NULL"
    if is_string:
        return f"'{esc(val)}'"
    return str(val)


def generate_movies_seed() -> None:
    if not _SPANISH_BENCH_CSV.exists():
        raise FileNotFoundError(
            f"{_SPANISH_BENCH_CSV} not found. "
            "Run notebook 8_Build_Benchmark_Dataset.ipynb first to generate it."
        )

    movies = pd.read_csv(_SPANISH_BENCH_CSV)
    movies = movies.sort_values("movie_id").reset_index(drop=True)

    with open(_DB_DIR / "seed_movies_benchmark.sql", "w", encoding="utf-8") as f:
        f.write("""INSERT INTO movies (
    tmdb_id, title, genres, overview, release_date,
    vote_average, vote_count, runtime, tagline,
    director, poster_path, backdrop_path, score
) VALUES\n""")

        values = []
        for _, row in movies.iterrows():
            genres_json = esc(to_json_genres(row["genres"]))
            release = sql_value(row["release_date"], is_string=True)
            vote_avg = sql_value(row["vote_average"])
            vote_count = sql_value(row["vote_count"])
            runtime = sql_value(row["runtime"])
            score = sql_value(row["score"])

            values.append(f"""(
    {int(row['tmdb_id'])},
    '{esc(row['title'])}',
    '{genres_json}',
    '{esc(row['overview'])}',
    {release},
    {vote_avg},
    {vote_count},
    {runtime},
    '{esc(row['tagline'])}',
    '{esc(row['director'])}',
    '{esc(row['poster_path'])}',
    '{esc(row['backdrop_path'])}',
    {score}
)""")

        f.write(",\n".join(values))
        f.write(";\n")

    print(f"Generated seed_movies_benchmark.sql ({len(movies)} movies)")


if __name__ == "__main__":
    generate_movies_seed()

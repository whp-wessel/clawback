# Pipelines

Reusable ETL and analysis code. Each pipeline lives in its own subdirectory with:

- A `manifest.yml` describing inputs, outputs, dependencies, and runtime requirements.
- Source code (Python, R, SQL, shell scripts, etc.).
- A locked dependency file (`requirements.txt`, `renv.lock`, etc.).

Pipelines are referenced by task specs and executed by agents in sandboxed environments.

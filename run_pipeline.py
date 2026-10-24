"""Executa os notebooks 01 a 07 em ordem, salvando as saídas dentro de cada notebook.

Uso (na raiz do projeto):  python run_pipeline.py
Para no primeiro notebook que falhar (o 07 falha se alguma validação crítica não passar).
"""
import subprocess
import sys
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent / "notebooks"

for nb in sorted(NB_DIR.glob("0*.ipynb")):
    print(f"==> executando {nb.name}", flush=True)
    r = subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
                        "--inplace", "--ExecutePreprocessor.timeout=1200", nb.name], cwd=NB_DIR)
    if r.returncode != 0:
        sys.exit(f"Falhou em {nb.name}")
print("Pipeline concluída. CSVs em output/dashboard/, relatório em relatorio_analitico.md")

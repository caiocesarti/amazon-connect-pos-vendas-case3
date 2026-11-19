#!/usr/bin/env python3
"""Gera o pacote de deploy `dist/pos_venda_fulfillment.zip` para a AWS Lambda (Python 3.12).

Inclui todos os módulos de `lambda/pos_venda_fulfillment/` e o dataset de fallback
`data/pos_venda_varejo.json` para alta disponibilidade.
"""

from __future__ import annotations

import contextlib
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_LAMBDA = RAIZ / "lambda" / "pos_venda_fulfillment"
ARQUIVO_DATASET = RAIZ / "data" / "pos_venda_varejo.json"
ARQUIVO_ZIP = RAIZ / "dist" / "pos_venda_fulfillment.zip"


def empacotar(destino: Path = ARQUIVO_ZIP) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for arq_py in sorted(PASTA_LAMBDA.glob("*.py")):
            zf.write(arq_py, arcname=arq_py.name)
        if ARQUIVO_DATASET.is_file():
            zf.write(ARQUIVO_DATASET, arcname="data/pos_venda_varejo.json")
    return destino


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(ValueError, OSError):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    pacote = empacotar()
    tamanho_kb = pacote.stat().st_size / 1024
    print(f"[LAMBDA PACKAGER] OK - Pacote criado em {pacote.as_posix()} ({tamanho_kb:.1f} KB).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

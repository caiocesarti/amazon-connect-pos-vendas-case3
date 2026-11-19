#!/usr/bin/env python3
"""Script de carga (seed) da tabela Amazon DynamoDB `PV-AssistenciasGarantia`.

Popula a tabela Single-Table com:
1. Rede de Assistências Técnicas Autorizadas (`pk = "ASSISTENCIA"`, `sk = "CEP#..."`)
2. Base de Notas Fiscais e Garantias (`pk = "NF#..."`, `sk = "PRODUTO#..."`)

Modos de uso:
    python scripts/seed_dynamodb.py --dry-run
    python scripts/seed_dynamodb.py --table PV-AssistenciasGarantia --region us-west-2
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_DATASET = RAIZ / "data" / "pos_venda_varejo.json"


def preparar_itens_seed(caminho: Path = ARQUIVO_DATASET) -> list[dict[str, Any]]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    itens: list[dict[str, Any]] = []
    for ast in dados.get("assistencias_tecnicas", []):
        itens.append({"entidade": "ASSISTENCIA_TECNICA", **ast})
    for nf in dados.get("notas_fiscais", []):
        itens.append({"entidade": "NOTA_FISCAL_GARANTIA", **nf})
    return itens


def executar_seed(
    nome_tabela: str,
    regiao: str,
    dry_run: bool = False,
    caminho: Path = ARQUIVO_DATASET,
) -> int:
    itens = preparar_itens_seed(caminho)
    if dry_run:
        print(
            f"[SEED DYNAMODB] DRY-RUN OK - {len(itens)} registros prontos para carga "
            f"na tabela '{nome_tabela}' ({regiao})."
        )
        return 0

    import boto3

    dynamodb = boto3.resource("dynamodb", region_name=regiao)
    tabela = dynamodb.Table(nome_tabela)
    with tabela.batch_writer() as batch:
        for item in itens:
            batch.put_item(Item=item)

    print(
        f"[SEED DYNAMODB] OK - {len(itens)} registros gravados com sucesso "
        f"na tabela '{nome_tabela}' ({regiao})."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(ValueError, OSError):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Popula a tabela DynamoDB PV-AssistenciasGarantia.")
    parser.add_argument(
        "--table",
        default=os.environ.get("DYNAMODB_TABLE", "PV-AssistenciasGarantia"),
        help="Nome da tabela DynamoDB.",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION", "us-west-2"),
        help="Região AWS.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas valida e exibe a contagem de itens sem conectar na AWS.",
    )
    args = parser.parse_args(argv)
    return executar_seed(nome_tabela=args.table, regiao=args.region, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

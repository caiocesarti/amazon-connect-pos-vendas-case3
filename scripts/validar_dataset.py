#!/usr/bin/env python3
"""Valida a integridade, o schema e a cobertura de casos de borda de `data/pos_venda_varejo.json`."""

from __future__ import annotations

import contextlib
import json
import re
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_PADRAO = RAIZ / "data" / "pos_venda_varejo.json"

CATEGORIAS_VALIDAS = {"LAVADORA", "GELADEIRA", "MICROONDAS", "FOGAO", "AR_CONDICIONADO"}
STATUS_GARANTIA_VALIDOS = {"ATIVA", "EXPIRADA"}


def validar_dataset(caminho: Path = ARQUIVO_PADRAO) -> tuple[bool, list[str]]:
    erros: list[str] = []
    if not caminho.is_file():
        return False, [f"Arquivo de dataset não encontrado: {caminho.as_posix()}"]

    try:
        dados: dict[str, Any] = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"JSON inválido em {caminho.name}: {exc}"]

    meta = dados.get("metadata") or {}
    if meta.get("tabela_dynamodb") not in {"PV-AssistenciasGarantia", "PV-AssistenciasGarantia"}:
        erros.append("metadata.tabela_dynamodb deve ser 'PV-AssistenciasGarantia'.")

    assistencias = dados.get("assistencias_tecnicas") or []
    if len(assistencias) < 6:
        erros.append("O dataset deve conter pelo menos 6 assistências técnicas autorizadas.")

    ids_ast: set[str] = set()
    for idx, ast in enumerate(assistencias, start=1):
        id_u = str(ast.get("id_unidade") or "")
        if not id_u:
            erros.append(f"Assistência #{idx} sem id_unidade.")
        elif id_u in ids_ast:
            erros.append(f"id_unidade duplicado: {id_u}")
        ids_ast.add(id_u)

        if ast.get("pk") != "ASSISTENCIA" or not str(ast.get("sk", "")).startswith("CEP#"):
            erros.append(f"Assistência {id_u} com pk/sk inválidos para Single-Table DynamoDB.")

        cep_ini = str(ast.get("cep_inicio", ""))
        cep_fim = str(ast.get("cep_fim", ""))
        if not (re.match(r"^\d{8}$", cep_ini) and re.match(r"^\d{8}$", cep_fim)):
            erros.append(f"Assistência {id_u} com cep_inicio/cep_fim fora do padrão de 8 dígitos.")
        elif int(cep_ini) > int(cep_fim):
            erros.append(f"Assistência {id_u} possui cep_inicio maior que cep_fim.")

        for campo_obrig in ("nome_fantasia", "cidade", "uf", "endereco", "telefone", "horario_atendimento"):
            if not str(ast.get(campo_obrig, "")).strip():
                erros.append(f"Assistência {id_u} sem campo obrigatório '{campo_obrig}'.")

        especs = ast.get("especialidades") or []
        if not especs or not set(especs).issubset(CATEGORIAS_VALIDAS):
            erros.append(f"Assistência {id_u} possui especialidades inválidas: {especs}")

    notas = dados.get("notas_fiscais") or []
    if len(notas) < 5:
        erros.append("O dataset deve conter pelo menos 5 notas fiscais simuladas.")

    tem_garantia_ativa = False
    tem_garantia_expirada = False
    tem_troca_elegivel = False
    tem_troca_fora_prazo = False

    nfs_vistas: set[str] = set()
    for idx, nf_item in enumerate(notas, start=1):
        nf = str(nf_item.get("nota_fiscal", ""))
        serie = str(nf_item.get("numero_serie", ""))
        if not re.match(r"^NF-\d{6}$", nf):
            erros.append(f"Nota #{idx} com formato inválido '{nf}' (esperado NF-XXXXXX).")
        if nf in nfs_vistas:
            erros.append(f"Nota Fiscal duplicada: {nf}")
        nfs_vistas.add(nf)

        if nf_item.get("pk") != f"NF#{nf}" or nf_item.get("sk") != f"PRODUTO#{serie}":
            erros.append(f"Nota {nf} com pk/sk inconsistentes.")

        cat = nf_item.get("categoria_produto")
        if cat not in CATEGORIAS_VALIDAS:
            erros.append(f"Nota {nf} com categoria_produto inválida: {cat}")

        status = nf_item.get("status_garantia")
        if status not in STATUS_GARANTIA_VALIDOS:
            erros.append(f"Nota {nf} com status_garantia inválido: {status}")
        if status == "ATIVA":
            tem_garantia_ativa = True
        elif status == "EXPIRADA":
            tem_garantia_expirada = True

        if nf_item.get("elegivel_troca_direta") is True:
            tem_troca_elegivel = True
        else:
            tem_troca_fora_prazo = True

    if not tem_garantia_ativa:
        erros.append("Dataset não possui caso de garantia ATIVA.")
    if not tem_garantia_expirada:
        erros.append("Dataset não possui caso de borda com garantia EXPIRADA.")
    if not tem_troca_elegivel:
        erros.append("Dataset não possui caso elegível para troca/devolução.")
    if not tem_troca_fora_prazo:
        erros.append("Dataset não possui caso de borda fora do prazo de troca.")

    sem_cobertura = dados.get("ceps_sem_cobertura_teste") or []
    if not sem_cobertura:
        erros.append("Dataset deve documentar CEPs/cidades sem cobertura para teste de transbordo.")

    return len(erros) == 0, erros


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(ValueError, OSError):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ok, erros = validar_dataset()
    if not ok:
        print("[DATASET] FALHA na validação de data/pos_venda_varejo.json:")
        for e in erros:
            print(f"  - {e}")
        return 1

    dados = json.loads(ARQUIVO_PADRAO.read_text(encoding="utf-8"))
    qtd_ast = len(dados["assistencias_tecnicas"])
    qtd_nf = len(dados["notas_fiscais"])
    print(
        f"[DATASET] OK - {qtd_ast} assistências autorizadas e {qtd_nf} notas fiscais validadas "
        "(incluindo todos os casos de borda do Case 3)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Valida estruturalmente os Contact Flows do Amazon Connect (`connect-flows/*.json`)."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FLOWS = RAIZ / "connect-flows"

FLUXOS_ESPERADOS = (
    "PV-Entrada-Principal.json",
    "PV-Transbordo-N1.json",
    "PV-Erro-Generico.json",
)


def validar_flows(pasta: Path = PASTA_FLOWS) -> tuple[bool, list[str]]:
    erros: list[str] = []
    for nome_arq in FLUXOS_ESPERADOS:
        arq = pasta / nome_arq
        if not arq.is_file():
            erros.append(f"Contact Flow obrigatório ausente: {nome_arq}")
            continue

        try:
            flow: dict[str, Any] = json.loads(arq.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            erros.append(f"JSON inválido em {nome_arq}: {exc}")
            continue

        if flow.get("Version") != "2019-10-30":
            erros.append(f"{nome_arq}: Version deve ser '2019-10-30'.")

        acoes = flow.get("Actions") or []
        ids_acoes = {a.get("Identifier") for a in acoes if a.get("Identifier")}
        start_action = flow.get("StartAction")
        if start_action not in ids_acoes:
            erros.append(f"{nome_arq}: StartAction '{start_action}' não existe em Actions.")

        tipos = [a.get("Type") for a in acoes]
        if "UpdateFlowLoggingBehavior" not in tipos:
            erros.append(f"{nome_arq}: Bloco UpdateFlowLoggingBehavior ausente.")
        if "DisconnectParticipant" not in tipos and "TransferContactToQueue" not in tipos:
            erros.append(f"{nome_arq}: Fluxo sem bloco de término/transferência.")

        if nome_arq == "PV-Entrada-Principal.json":
            for tipo_obrig in (
                "UpdateContactTextToSpeechVoice",
                "UpdateContactData",
                "CreateWisdomSession",
                "ConnectParticipantWithLexBot",
                "UpdateContactAttributes",
            ):
                if tipo_obrig not in tipos:
                    erros.append(f"{nome_arq}: Bloco obrigatório '{tipo_obrig}' ausente.")

        if nome_arq == "PV-Transbordo-N1.json":
            for tipo_obrig in (
                "UpdateContactAttributes",
                "UpdateContactTargetQueue",
                "CheckHoursOfOperation",
                "TransferContactToQueue",
            ):
                if tipo_obrig not in tipos:
                    erros.append(f"{nome_arq}: Bloco obrigatório '{tipo_obrig}' ausente.")

    return len(erros) == 0, erros


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(ValueError, OSError):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ok, erros = validar_flows()
    if not ok:
        print("[FLOWS] FALHA na validação dos Contact Flows:")
        for e in erros:
            print(f"  - {e}")
        return 1

    print(f"[FLOWS] OK - {len(FLUXOS_ESPERADOS)} Contact Flows validados no schema 2019-10-30.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

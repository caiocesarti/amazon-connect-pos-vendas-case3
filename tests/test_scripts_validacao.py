"""Testes automatizados dos scripts de governança DevSecOps, Dataset, Contact Flows e FinOps."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import empacotar_lambda  # noqa: E402
import injetar_widget  # noqa: E402
import seed_dynamodb  # noqa: E402
import validar_dataset  # noqa: E402
import validar_flows  # noqa: E402
import verificar_segredos  # noqa: E402


def test_validacao_dataset_integra() -> None:
    ok, erros = validar_dataset.validar_dataset()
    assert ok is True, f"Erros no dataset: {erros}"


def test_validacao_contact_flows() -> None:
    ok, erros = validar_flows.validar_flows()
    assert ok is True, f"Erros nos flows: {erros}"


def test_seed_dynamodb_dry_run() -> None:
    itens = seed_dynamodb.preparar_itens_seed()
    assert len(itens) >= 20
    rc = seed_dynamodb.executar_seed("PV-AssistenciasGarantia", "us-east-1", dry_run=True)
    assert rc == 0


def test_gerador_loader_finops_widget() -> None:
    snippet_exemplo = (RAIZ / "landing" / "widget-snippet.example.html").read_text(encoding="utf-8")
    codigo = injetar_widget.gerar_codigo_loader_finops(snippet_exemplo, limite_mensagens=25)
    assert "navigator.webdriver" in codigo
    assert "pv_aws_connect_msg_count_v1" in codigo
    assert "var MAX_MSG = 25;" in codigo
    assert "Cliente EletroLar" in codigo


def test_empacotar_lambda_gera_zip(tmp_path: Path) -> None:
    alvo_zip = tmp_path / "pos_venda_fulfillment.zip"
    gerado = empacotar_lambda.empacotar(destino=alvo_zip)
    assert gerado.is_file()
    assert gerado.stat().st_size > 2000


def test_scanner_zero_leak_detecta_chaves_e_aprova_placeholders() -> None:
    achados_limpos = verificar_segredos.analisar_texto(
        "arn:aws:lambda:us-east-1:000000000000:function:PV-PosVendaFulfillment",
        "connect-flows/PV-Entrada-Principal.json",
    )
    assert achados_limpos == []

    conta_simulada = "123456" + "789012"
    achados_vazamento = verificar_segredos.analisar_texto(
        f"arn:aws:lambda:us-east-1:{conta_simulada}:function:RealAccount",
        "connect-flows/teste.json",
    )
    assert len(achados_vazamento) >= 1
    assert achados_vazamento[0].regra in {"AWS_ARN_CONTA_REAL", "AWS_ACCOUNT_ID"}

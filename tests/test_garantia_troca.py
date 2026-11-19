"""Testes unitários de Acionamento de Garantia (Cenário 1) e Troca/Devolução (Cenário 3)."""

from __future__ import annotations

from unittest.mock import MagicMock

from garantia_troca import (
    consultar_nota_fiscal,
    gerar_protocolo_deterministico,
    normalizar_nota_fiscal,
    normalizar_numero_serie,
    processar_acionamento_garantia,
    processar_troca_devolucao,
)


def test_protocolo_deterministico_idempotente() -> None:
    p1 = gerar_protocolo_deterministico("GARANTIA", "NF-100201:EL-LAV-2026-8841", data_iso="2026-11-18")
    p2 = gerar_protocolo_deterministico("GARANTIA", "NF-100201:EL-LAV-2026-8841", data_iso="20261118")
    assert p1 == p2
    assert p1.startswith("PV-20261118-")
    assert len(p1) == 16


def test_normalizacao_nf_e_numero_serie() -> None:
    assert normalizar_nota_fiscal("minha nota é nf 100201") == "NF-100201"
    assert normalizar_nota_fiscal("100203") == "NF-100203"
    assert normalizar_nota_fiscal("sem numero") is None
    assert normalizar_numero_serie("série el-lav-2026-8841") == "EL-LAV-2026-8841"
    assert normalizar_numero_serie("SERIE12345") == "SERIE12345"
    assert normalizar_numero_serie(None) is None


def test_cenario1_garantia_ativa_sucesso() -> None:
    res = processar_acionamento_garantia(
        modelo_produto="Lavadora 12kg",
        numero_serie="EL-LAV-2026-8841",
        nota_fiscal="NF-100201",
        descricao_defeito="Parou de funcionar completamente",
        data_iso="2026-11-18",
    )
    assert res["acionada"] is True
    assert res["status_garantia"] == "ATIVA"
    assert res["transbordo"] is False
    assert res["assistencia_vinculada"] is not None
    assert res["assistencia_vinculada"]["id_unidade"] == "AST-SP-01"
    assert res["protocolo"].startswith("PV-20261118-")


def test_cenario1_borda_garantia_expirada_aciona_transbordo() -> None:
    res = processar_acionamento_garantia(
        modelo_produto="Geladeira FrostFree",
        numero_serie="EL-GEL-2024-1102",
        nota_fiscal="NF-100202",
        descricao_defeito="Não está gelando a parte de baixo",
    )
    assert res["acionada"] is False
    assert res["status_garantia"] == "EXPIRADA"
    assert res["transbordo"] is True
    assert res["motivo_transbordo"] == "GARANTIA_EXPIRADA"


def test_cenario1_borda_cep_sem_posto_local() -> None:
    res = processar_acionamento_garantia(
        modelo_produto="Geladeira Inverse",
        numero_serie="EL-GEL-2026-4410",
        nota_fiscal="NF-100207",
        descricao_defeito="Painel piscando",
    )
    assert res["acionada"] is True
    assert res["status_garantia"] == "ATIVA"
    assert res["assistencia_vinculada"] is None
    assert res["transbordo"] is True
    assert res["motivo_transbordo"] == "CEP_SEM_ASSISTENCIA"


def test_cenario1_borda_nf_nao_encontrada() -> None:
    res = processar_acionamento_garantia(
        modelo_produto="Lavadora 10kg",
        numero_serie="EL-LAV-2026-0000",
        nota_fiscal="NF-999999",
        descricao_defeito="Não liga",
    )
    assert res["acionada"] is False
    assert res["status_garantia"] == "NAO_ENCONTRADA"
    assert res["transbordo"] is True
    assert res["motivo_transbordo"] == "NF_NAO_LOCALIZADA"


def test_cenario3_troca_devolucao_elegivel_7dias() -> None:
    res = processar_troca_devolucao(
        nota_fiscal="NF-100203",
        modelo_produto="Micro-ondas 32L",
        motivo_solicitacao="Arrependimento 7 dias",
        data_iso="2026-11-18",
    )
    assert res["caso_criado"] is True
    assert res["elegibilidade"] == "ELEGIVEL"
    assert res["transbordo"] is False
    assert res["protocolo"].startswith("PV-20261118-")


def test_cenario3_borda_troca_fora_do_prazo_90dias() -> None:
    res = processar_troca_devolucao(
        nota_fiscal="NF-100204",
        modelo_produto="Lava e Seca 11kg",
        motivo_solicitacao="Quero devolver",
    )
    assert res["caso_criado"] is True
    assert res["elegibilidade"] == "FORA_DO_PRAZO"
    assert res["transbordo"] is True
    assert res["motivo_transbordo"] == "FORA_PRAZO_TROCA"


def test_cenario3_borda_nf_inexistente() -> None:
    res = processar_troca_devolucao(
        nota_fiscal="NF-888888",
        modelo_produto="Fogão 4 bocas",
        motivo_solicitacao="Veio amassado",
    )
    assert res["caso_criado"] is False
    assert res["elegibilidade"] == "EXIGE_ANALISE_N1"
    assert res["transbordo"] is True


def test_consultar_nf_com_mock_dynamodb() -> None:
    tabela_mock = MagicMock()
    tabela_mock.get_item.return_value = {
        "Item": {
            "nota_fiscal": "NF-100201",
            "numero_serie": "EL-LAV-2026-8841",
            "modelo_produto": "Lavadora Mock",
            "status_garantia": "ATIVA",
        }
    }
    item = consultar_nota_fiscal("NF-100201", "EL-LAV-2026-8841", tabela_dynamodb=tabela_mock)
    assert item is not None
    assert item["modelo_produto"] == "Lavadora Mock"


def test_nf_tolera_texto_colado_pelo_slot_alphanumeric() -> None:
    assert normalizar_nota_fiscal('NF-100201PAROUDEFUNCIONAR') == 'NF-100201'
    assert normalizar_numero_serie('EL-LAV2026-8841') == 'EL-LAV-2026-8841'

"""Testes unitários do motor de localização de Assistências Técnicas Autorizadas (Cenário 2 do PDF)."""

from __future__ import annotations

from unittest.mock import MagicMock

from assistencia import (
    buscar_assistencia_mais_proxima,
    extrair_cep,
    normalizar_categoria,
    normalizar_cidade,
    remover_acentos,
)


def test_remover_acentos_e_normalizar_cidade() -> None:
    assert remover_acentos("São Paulo") == "sao paulo"
    assert normalizar_cidade("Moro em São Paulo/SP") == "sao paulo"
    assert normalizar_cidade("ssa") == "salvador"
    assert normalizar_cidade("bh") == "belo horizonte"
    assert normalizar_cidade("") == ""


def test_extrair_cep_formatos_variados() -> None:
    assert extrair_cep("Meu CEP é 01310-200 em SP") == "01310200"
    assert extrair_cep("41820020") == "41820020"
    assert extrair_cep("Salvador Bahia") is None
    assert extrair_cep(None) is None


def test_normalizar_categoria_sinonimos_populares() -> None:
    assert normalizar_categoria("máquina de lavar roupa") == "LAVADORA"
    assert normalizar_categoria("lava e seca 11kg") == "LAVADORA"
    assert normalizar_categoria("geladeira frost free") == "GELADEIRA"
    assert normalizar_categoria("forno micro-ondas") == "MICROONDAS"
    assert normalizar_categoria("fogão 5 bocas") == "FOGAO"
    assert normalizar_categoria("ar-condicionado split") == "AR_CONDICIONADO"
    assert normalizar_categoria("LAVADORA") == "LAVADORA"
    assert normalizar_categoria("televisor") is None
    assert normalizar_categoria(None) is None


def test_buscar_assistencia_por_cep_sao_paulo() -> None:
    res = buscar_assistencia_mais_proxima("01310-200", "máquina de lavar")
    assert res["encontrada"] is True
    assert res["criterio_busca"] == "CEP"
    assert res["unidade_principal"]["id_unidade"] == "AST-SP-01"
    assert res["transbordo_recomendado"] is False


def test_buscar_assistencia_por_cidade_salvador() -> None:
    res = buscar_assistencia_mais_proxima("Salvador - BA", "geladeira")
    assert res["encontrada"] is True
    assert res["criterio_busca"] == "CIDADE"
    assert res["unidade_principal"]["id_unidade"] == "AST-BA-01"
    assert "3341-8800" in res["unidade_principal"]["telefone"]


def test_buscar_assistencia_caso_borda_cep_sem_cobertura() -> None:
    res = buscar_assistencia_mais_proxima("69900-000", "GELADEIRA")
    assert res["encontrada"] is False
    assert res["unidade_principal"] is None
    assert res["transbordo_recomendado"] is True
    assert res["motivo_transbordo"] == "CEP_SEM_ASSISTENCIA"


def test_buscar_assistencia_com_mock_dynamodb() -> None:
    tabela_mock = MagicMock()
    tabela_mock.query.return_value = {
        "Items": [
            {
                "id_unidade": "AST-MOCK-01",
                "nome_fantasia": "Autorizada Mock DynamoDB",
                "cidade": "Curitiba",
                "cidade_normalizada": "curitiba",
                "uf": "PR",
                "cep_inicio": "80000000",
                "cep_fim": "82999999",
                "endereco": "Av. Batel, 100",
                "telefone": "(41) 3000-0000",
                "horario_atendimento": "Seg a Sex 08h-18h",
                "especialidades": ["LAVADORA"],
            }
        ]
    }
    res = buscar_assistencia_mais_proxima("80250-210", "LAVADORA", tabela_dynamodb=tabela_mock)
    assert res["encontrada"] is True
    assert res["unidade_principal"]["id_unidade"] == "AST-MOCK-01"

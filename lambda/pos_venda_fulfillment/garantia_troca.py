"""Regras de negócio para Acionamento Automático de Garantia e Solicitação de Troca/Devolução.

Atende aos Cenários 1 e 3 do PDF do Case 3:
- Cenário 1 (Defeito no produto): Coleta modelo, número de série e nota fiscal, valida o status
  da garantia no DynamoDB/JSON e aciona a garantia automaticamente gerando protocolo `PV-YYYYMMDD-XXXX`.
- Cenário 3 (Troca / devolução): Coleta nota fiscal, modelo e motivo, valida elegibilidade
  (CDC 7 dias ou avaria/defeito inicial), cria o caso e envia o protocolo no chat online.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from typing import Any

from assistencia import buscar_assistencia_mais_proxima, carregar_dataset_local, normalizar_categoria


def gerar_protocolo_deterministico(
    tipo: str,
    referencia: str,
    data_iso: str | None = None,
) -> str:
    """Gera protocolo idempotente no formato `PV-YYYYMMDD-XXXX`."""
    if data_iso and re.match(r"^\d{8}$", data_iso):
        bloco_data = data_iso
    elif data_iso and re.match(r"^\d{4}-\d{2}-\d{2}", data_iso):
        bloco_data = data_iso[:10].replace("-", "")
    else:
        bloco_data = datetime.now(timezone.utc).strftime("%Y%m%d")

    semente = f"{tipo.strip().upper()}::{referencia.strip().upper()}::{bloco_data}"
    digest = hashlib.sha256(semente.encode("utf-8")).hexdigest()
    sufixo_num = int(digest[:8], 16) % 9000 + 1000
    return f"PV-{bloco_data}-{sufixo_num}"


def normalizar_nota_fiscal(valor: str | None) -> str | None:
    """Extrai e padroniza o código da Nota Fiscal no formato `NF-XXXXXX`."""
    if not valor:
        return None
    texto = valor.strip().upper()
    # Tolera lixo colado pelo slot AlphaNumeric do Lex (ex.: "NF-100201PAROUDEFUNCIONAR")
    match = re.search(r"(?<!\d)(\d{5,9})(?!\d)", texto)
    if match:
        return f"NF-{match.group(1)}"
    return None


def normalizar_numero_serie(valor: str | None) -> str | None:
    """Extrai e padroniza o Número de Série no formato `EL-XXX-YYYY-ZZZZ` ou alfanumérico."""
    if not valor:
        return None
    texto = valor.strip().upper()
    match_padrao = re.search(r"\bEL[\s\-]?([A-Z]{3})[\s\-]?(\d{4})[\s\-]?(\d{4})\b", texto)
    if match_padrao:
        return "EL-" + "-".join(match_padrao.groups())
    # Aceita também códigos alfanuméricos de série com pelo menos 6 caracteres contendo dígitos
    candidatos = re.findall(r"\b[A-Z0-9\-]{6,20}\b", texto)
    for cand in candidatos:
        if any(c.isdigit() for c in cand) and not cand.startswith("NF"):
            return cand
    return None


def consultar_nota_fiscal(
    nota_fiscal: str,
    numero_serie: str | None = None,
    tabela_dynamodb: Any | None = None,
) -> dict[str, Any] | None:
    """Busca registro da Nota Fiscal no DynamoDB (quando habilitado) ou no dataset local."""
    nf_norm = normalizar_nota_fiscal(nota_fiscal)
    if not nf_norm:
        return None
    serie_norm = normalizar_numero_serie(numero_serie) if numero_serie else None

    usar_dynamo = os.environ.get("USE_DYNAMODB", "false").lower() == "true"
    if tabela_dynamodb is not None or usar_dynamo:
        try:
            if tabela_dynamodb is None:
                import boto3

                nome_tabela = os.environ.get("DYNAMODB_TABLE", "PV-AssistenciasGarantia")
                regiao = os.environ.get("AWS_REGION", "us-west-2")
                tabela_dynamodb = boto3.resource("dynamodb", region_name=regiao).Table(nome_tabela)

            from boto3.dynamodb.conditions import Key

            pk_val = f"NF#{nf_norm}"
            if serie_norm:
                resp = tabela_dynamodb.get_item(
                    Key={"pk": pk_val, "sk": f"PRODUTO#{serie_norm}"}
                )
                if "Item" in resp:
                    return dict(resp["Item"])
            resp_q = tabela_dynamodb.query(KeyConditionExpression=Key("pk").eq(pk_val))
            itens = resp_q.get("Items", [])
            if itens:
                return dict(itens[0])
        except Exception:
            pass

    dados = carregar_dataset_local()
    for item in dados.get("notas_fiscais", []):
        if item.get("nota_fiscal", "").upper() == nf_norm:
            if serie_norm and item.get("numero_serie", "").upper() != serie_norm:
                # Continua procurando caso a NF tenha múltiplos itens, ou retorna o item da NF
                pass
            return dict(item)
    return None


def _registrar_caso_dynamodb(caso: dict[str, Any], tabela_dynamodb: Any | None = None) -> bool:
    """Persiste o caso gerado na tabela `PV-AssistenciasGarantia` quando o DynamoDB está ativo."""
    usar_dynamo = os.environ.get("USE_DYNAMODB", "false").lower() == "true"
    if tabela_dynamodb is None and not usar_dynamo:
        return False
    try:
        if tabela_dynamodb is None:
            import boto3

            nome_tabela = os.environ.get("DYNAMODB_TABLE", "PV-AssistenciasGarantia")
            regiao = os.environ.get("AWS_REGION", "us-west-2")
            tabela_dynamodb = boto3.resource("dynamodb", region_name=regiao).Table(nome_tabela)

        item_db = {
            "pk": f"CASO#{caso['protocolo']}",
            "sk": f"NF#{caso['nota_fiscal']}",
            **caso,
        }
        tabela_dynamodb.put_item(Item=item_db)
        return True
    except Exception:
        return False


def processar_acionamento_garantia(
    modelo_produto: str,
    numero_serie: str,
    nota_fiscal: str,
    descricao_defeito: str,
    tabela_dynamodb: Any | None = None,
    data_iso: str | None = None,
) -> dict[str, Any]:
    """Valida NF e Série e aciona automaticamente o fluxo de garantia (Cenário 1)."""
    nf_norm = normalizar_nota_fiscal(nota_fiscal) or nota_fiscal.strip().upper()
    serie_norm = normalizar_numero_serie(numero_serie) or numero_serie.strip().upper()
    registro = consultar_nota_fiscal(nf_norm, serie_norm, tabela_dynamodb=tabela_dynamodb)

    protocolo = gerar_protocolo_deterministico(
        "GARANTIA", f"{nf_norm}:{serie_norm}", data_iso=data_iso
    )

    if not registro:
        return {
            "acionada": False,
            "status_garantia": "NAO_ENCONTRADA",
            "protocolo": protocolo,
            "nota_fiscal": nf_norm,
            "numero_serie": serie_norm,
            "modelo_produto": modelo_produto.strip(),
            "categoria_produto": normalizar_categoria(modelo_produto) or "LAVADORA",
            "descricao_defeito": descricao_defeito.strip(),
            "garantia_ate": None,
            "assistencia_vinculada": None,
            "transbordo": True,
            "motivo_transbordo": "NF_NAO_LOCALIZADA",
        }

    modelo_oficial = registro.get("modelo_produto") or modelo_produto.strip()
    categoria_oficial = registro.get("categoria_produto") or normalizar_categoria(modelo_oficial) or "LAVADORA"
    serie_oficial = registro.get("numero_serie") or serie_norm
    status_garantia = registro.get("status_garantia", "ATIVA").upper()
    garantia_ate = registro.get("garantia_ate", "")
    cep_cliente = registro.get("cep_cliente", "")

    if status_garantia != "ATIVA":
        return {
            "acionada": False,
            "status_garantia": "EXPIRADA",
            "protocolo": protocolo,
            "nota_fiscal": nf_norm,
            "numero_serie": serie_oficial,
            "modelo_produto": modelo_oficial,
            "categoria_produto": categoria_oficial,
            "cliente_nome": registro.get("cliente_nome", "Cliente EletroLar"),
            "descricao_defeito": descricao_defeito.strip(),
            "garantia_ate": garantia_ate,
            "assistencia_vinculada": None,
            "transbordo": True,
            "motivo_transbordo": "GARANTIA_EXPIRADA",
        }

    busca_ast = buscar_assistencia_mais_proxima(
        cep_ou_cidade=cep_cliente or registro.get("cidade_cliente", ""),
        categoria_produto=categoria_oficial,
        tabela_dynamodb=tabela_dynamodb,
    )
    unidade_ast = busca_ast.get("unidade_principal")

    caso = {
        "protocolo": protocolo,
        "tipo_solicitacao": "ACIONAMENTO_GARANTIA",
        "nota_fiscal": nf_norm,
        "numero_serie": serie_oficial,
        "modelo_produto": modelo_oficial,
        "categoria_produto": categoria_oficial,
        "descricao_defeito": descricao_defeito.strip(),
        "status_caso": "ABERTO_AUTOMATICO" if unidade_ast else "ENCAMINHADO_LOGISTICA_N1",
        "criado_em_iso": datetime.now(timezone.utc).isoformat(),
    }
    _registrar_caso_dynamodb(caso, tabela_dynamodb=tabela_dynamodb)

    # Caso o CEP do cliente não tenha posto autorizado presencial (ex.: NF-100207 em Rio Branco/AC),
    # a garantia é acionada com protocolo, mas sinaliza transbordo para agendar logística reversa.
    sem_posto_local = unidade_ast is None

    return {
        "acionada": True,
        "status_garantia": "ATIVA",
        "protocolo": protocolo,
        "nota_fiscal": nf_norm,
        "numero_serie": serie_oficial,
        "modelo_produto": modelo_oficial,
        "categoria_produto": categoria_oficial,
        "cliente_nome": registro.get("cliente_nome", "Cliente EletroLar"),
        "descricao_defeito": descricao_defeito.strip(),
        "garantia_ate": garantia_ate,
        "assistencia_vinculada": unidade_ast,
        "transbordo": sem_posto_local,
        "motivo_transbordo": "CEP_SEM_ASSISTENCIA" if sem_posto_local else None,
    }


def processar_troca_devolucao(
    nota_fiscal: str,
    modelo_produto: str,
    motivo_solicitacao: str,
    tabela_dynamodb: Any | None = None,
    data_iso: str | None = None,
) -> dict[str, Any]:
    """Cria caso de Troca ou Devolução e gera protocolo para envio no chat online (Cenário 3)."""
    nf_norm = normalizar_nota_fiscal(nota_fiscal) or nota_fiscal.strip().upper()
    registro = consultar_nota_fiscal(nf_norm, tabela_dynamodb=tabela_dynamodb)
    protocolo = gerar_protocolo_deterministico(
        "TROCA", f"{nf_norm}:{motivo_solicitacao}", data_iso=data_iso
    )

    if not registro:
        return {
            "caso_criado": False,
            "elegibilidade": "EXIGE_ANALISE_N1",
            "protocolo": protocolo,
            "nota_fiscal": nf_norm,
            "modelo_produto": modelo_produto.strip(),
            "categoria_produto": normalizar_categoria(modelo_produto) or "ELETRODOMESTICO",
            "motivo_solicitacao": motivo_solicitacao.strip(),
            "dias_desde_compra": None,
            "motivo_bloqueio": "Nota Fiscal não localizada na base automática.",
            "transbordo": True,
            "motivo_transbordo": "NF_NAO_LOCALIZADA",
        }

    modelo_oficial = registro.get("modelo_produto") or modelo_produto.strip()
    categoria_oficial = registro.get("categoria_produto") or normalizar_categoria(modelo_oficial) or "LAVADORA"
    elegivel = bool(registro.get("elegivel_troca_direta", False))
    dias_compra = registro.get("dias_desde_compra", 0)
    motivo_bloqueio = registro.get("motivo_inelegibilidade_troca")

    caso = {
        "protocolo": protocolo,
        "tipo_solicitacao": "TROCA_DEVOLUCAO",
        "nota_fiscal": nf_norm,
        "numero_serie": registro.get("numero_serie", "N/A"),
        "modelo_produto": modelo_oficial,
        "categoria_produto": categoria_oficial,
        "motivo_solicitacao": motivo_solicitacao.strip(),
        "status_caso": "APROVADO_COLETA_REVERSA" if elegivel else "ENCAMINHADO_ANALISE_N1",
        "criado_em_iso": datetime.now(timezone.utc).isoformat(),
    }
    _registrar_caso_dynamodb(caso, tabela_dynamodb=tabela_dynamodb)

    if not elegivel:
        return {
            "caso_criado": True,
            "elegibilidade": "FORA_DO_PRAZO",
            "protocolo": protocolo,
            "nota_fiscal": nf_norm,
            "numero_serie": registro.get("numero_serie", ""),
            "modelo_produto": modelo_oficial,
            "categoria_produto": categoria_oficial,
            "cliente_nome": registro.get("cliente_nome", "Cliente EletroLar"),
            "motivo_solicitacao": motivo_solicitacao.strip(),
            "dias_desde_compra": dias_compra,
            "status_garantia": registro.get("status_garantia", "ATIVA"),
            "motivo_bloqueio": motivo_bloqueio,
            "transbordo": True,
            "motivo_transbordo": "FORA_PRAZO_TROCA",
        }

    return {
        "caso_criado": True,
        "elegibilidade": "ELEGIVEL",
        "protocolo": protocolo,
        "nota_fiscal": nf_norm,
        "numero_serie": registro.get("numero_serie", ""),
        "modelo_produto": modelo_oficial,
        "categoria_produto": categoria_oficial,
        "cliente_nome": registro.get("cliente_nome", "Cliente EletroLar"),
        "motivo_solicitacao": motivo_solicitacao.strip(),
        "dias_desde_compra": dias_compra,
        "status_garantia": registro.get("status_garantia", "ATIVA"),
        "motivo_bloqueio": None,
        "transbordo": False,
        "motivo_transbordo": None,
    }

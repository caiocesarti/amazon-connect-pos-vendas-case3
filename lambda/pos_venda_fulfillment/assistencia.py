"""Motor de consulta de Assistências Técnicas Autorizadas no Amazon DynamoDB (com fallback JSON).

Atende ao Cenário 2 do PDF do Case 3:
- Localiza a assistência autorizada mais próxima com base no CEP (faixa de 8 dígitos)
  ou nome da cidade informado pelo cliente.
- Filtra opcionalmente pela especialidade/categoria do eletrodoméstico.
- Em caso de CEP ou município sem cobertura local, aciona fluxo alternativo com
  contexto preservado para transbordo ao agente humano N1.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

CAMINHO_DATASET_PADRAO = Path(__file__).resolve().parent.parent.parent / "data" / "pos_venda_varejo.json"

_MAPA_SINONIMOS_CIDADE: dict[str, str] = {
    "sp": "sao paulo",
    "sampa": "sao paulo",
    "sao paulo capital": "sao paulo",
    "ssa": "salvador",
    "salvador bahia": "salvador",
    "lauro": "lauro de freitas",
    "feira": "feira de santana",
    "rj": "rio de janeiro",
    "rio": "rio de janeiro",
    "bh": "belo horizonte",
    "belzonte": "belo horizonte",
    "cwb": "curitiba",
    "poa": "porto alegre",
    "bsb": "brasilia",
    "df": "brasilia",
}

_MAPA_CATEGORIAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("LAVADORA", ("lavadora", "maquina de lavar", "lava e seca", "tanquinho", "centrifuga", "secadora")),
    ("GELADEIRA", ("geladeira", "refrigerador", "freezer", "frost free", "frostfree", "inverse", "side by side")),
    ("MICROONDAS", ("microondas", "micro-ondas", "micro ondas", "forno eletrico")),
    ("FOGAO", ("fogao", "cooktop", "forno a gas", "cinco bocas", "4 bocas", "5 bocas")),
    ("AR_CONDICIONADO", ("ar condicionado", "ar-condicionado", "split", "climatizador", "inverter 12000", "btus")),
)


def remover_acentos(texto: str) -> str:
    """Normaliza string para ASCII minúsculo sem acentuação."""
    nfkd = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def extrair_cep(texto: str | None) -> str | None:
    """Extrai CEP de 8 dígitos numéricos de uma entrada livre (ex.: '01310-200' -> '01310200')."""
    if not texto:
        return None
    match = re.search(r"\b(\d{5})[\s.-]?(\d{3})\b", texto)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    apenas_digitos = re.sub(r"\D", "", texto)
    if len(apenas_digitos) == 8:
        return apenas_digitos
    return None


def normalizar_cidade(texto: str | None) -> str:
    """Normaliza cidade removendo UF sufixada, palavras de ligação e aplicando sinônimos."""
    if not texto:
        return ""
    base = remover_acentos(texto)
    # Remove prefixos conversacionais comuns ("moro em", "sou de", "cidade de")
    base = re.sub(
        r"^(?:eu\s+)?(?:moro\s+em|sou\s+de|estou\s+em|preciso\s+em|assistencia\s+em|cidade\s+de|municipio\s+de|cep)\s+",
        "",
        base,
    ).strip()
    # Remove sufixo de UF como "/sp", "- ba", ", rj"
    base = re.sub(r"[\s,/|-]+(?:sp|ba|rj|mg|pr|rs|df|ac|ro|al|pe|ce|go|sc|es|am|pa)$", "", base).strip()
    base = re.sub(r"[^a-z0-9\s]", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    return _MAPA_SINONIMOS_CIDADE.get(base, base)


def normalizar_categoria(texto: str | None) -> str | None:
    """Converte descrição popular do eletrodoméstico na categoria canônica."""
    if not texto:
        return None
    norm = remover_acentos(texto)
    if norm.upper() in {"LAVADORA", "GELADEIRA", "MICROONDAS", "FOGAO", "AR_CONDICIONADO"}:
        return norm.upper()
    for categoria, termos in _MAPA_CATEGORIAS:
        if any(termo in norm for termo in termos):
            return categoria
    return None


@lru_cache(maxsize=2)
def carregar_dataset_local(caminho: str | None = None) -> dict[str, Any]:
    """Carrega o JSON local de pós-venda (usado como fallback ou em testes offline)."""
    alvo = Path(caminho) if caminho else CAMINHO_DATASET_PADRAO
    with alvo.open("r", encoding="utf-8") as arq:
        return json.load(arq)


def _obter_assistencias(tabela_dynamodb: Any | None = None) -> list[dict[str, Any]]:
    """Obtém a lista de assistências técnicas via DynamoDB (se configurado) ou fallback JSON."""
    usar_dynamo = os.environ.get("USE_DYNAMODB", "false").lower() == "true"
    if tabela_dynamodb is not None or usar_dynamo:
        try:
            if tabela_dynamodb is None:
                import boto3

                nome_tabela = os.environ.get("DYNAMODB_TABLE", "PV-AssistenciasGarantia")
                regiao = os.environ.get("AWS_REGION", "us-west-2")
                recurso = boto3.resource("dynamodb", region_name=regiao)
                tabela_dynamodb = recurso.Table(nome_tabela)

            from boto3.dynamodb.conditions import Key

            resp = tabela_dynamodb.query(KeyConditionExpression=Key("pk").eq("ASSISTENCIA"))
            itens = resp.get("Items", [])
            if itens:
                return list(itens)
        except Exception:
            # Fallback resiliente para o dataset embarcado caso a tabela não esteja acessível
            pass

    dados = carregar_dataset_local()
    return list(dados.get("assistencias_tecnicas", []))


def buscar_assistencia_mais_proxima(
    cep_ou_cidade: str,
    categoria_produto: str | None = None,
    tabela_dynamodb: Any | None = None,
) -> dict[str, Any]:
    """Localiza a assistência técnica autorizada mais próxima por CEP ou Cidade."""
    unidades = _obter_assistencias(tabela_dynamodb=tabela_dynamodb)
    categoria_norm = normalizar_categoria(categoria_produto)
    cep_extraido = extrair_cep(cep_ou_cidade)
    cidade_norm = normalizar_cidade(cep_ou_cidade) if not cep_extraido else ""

    candidatas: list[dict[str, Any]] = []
    criterio_usado = "CEP" if cep_extraido else "CIDADE"

    if cep_extraido:
        cep_num = int(cep_extraido)
        for u in unidades:
            inicio = int(str(u.get("cep_inicio", "00000000")))
            fim = int(str(u.get("cep_fim", "99999999")))
            if inicio <= cep_num <= fim:
                candidatas.append(u)
    elif cidade_norm:
        for u in unidades:
            cid_u = u.get("cidade_normalizada") or remover_acentos(u.get("cidade", ""))
            if cid_u == cidade_norm or (len(cidade_norm) >= 4 and cidade_norm in cid_u):
                candidatas.append(u)

    if not candidatas:
        return {
            "encontrada": False,
            "criterio_busca": criterio_usado,
            "localidade_informada": cep_extraido or cep_ou_cidade.strip(),
            "categoria_filtrada": categoria_norm,
            "unidade_principal": None,
            "unidades_adicionais": [],
            "transbordo_recomendado": True,
            "motivo_transbordo": "CEP_SEM_ASSISTENCIA",
        }

    # Se o cliente especificou categoria (ex.: AR_CONDICIONADO), prioriza unidades que atendem a especialidade
    if categoria_norm:
        com_especialidade = [
            u for u in candidatas if categoria_norm in (u.get("especialidades") or [])
        ]
        if com_especialidade:
            candidatas = com_especialidade

    principal = candidatas[0]
    adicionais = candidatas[1:3]

    return {
        "encontrada": True,
        "criterio_busca": criterio_usado,
        "localidade_informada": cep_extraido or principal.get("cidade", cep_ou_cidade),
        "categoria_filtrada": categoria_norm,
        "unidade_principal": principal,
        "unidades_adicionais": adicionais,
        "transbordo_recomendado": False,
        "motivo_transbordo": None,
    }

"""Guardrails de segurança operacional, elétrica e conversacional para o Pós-Venda EletroLar.

Camadas implementadas:
1. Detecção de risco elétrico, incêndio ou vazamento doméstico (fumaça, cheiro de queimado,
   faísca, choque elétrico, fogo, vazamento de gás) -> aciona orientação de emergência e
   transbordo imediato para especialista humano N1.
2. Prevenção de reparo caseiro (DIY) que viole a garantia de 12 meses ou exponha o cliente
   a alta tensão (ex.: capacitor de micro-ondas, placa inverter).
3. Sanitização e bloqueio de tentativas de Prompt Injection / Jailbreak.
"""

from __future__ import annotations

import re
from typing import Any

TAMANHO_MAXIMO_ENTRADA = 600

_PADROES_PROMPT_INJECTION: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bignore\s+(?:all\s+|todas\s+as\s+)?(?:previous\s+|anteriores\s+)?(?:instructions|instru[cç][oõ]es)"),
    re.compile(r"(?i)\b(?:system\s+prompt|prompt\s+do\s+sistema|jailbreak|dan\s+mode)\b"),
    re.compile(r"(?i)\b(?:voc[eê]\s+agora\s+[eé]\s+um|aja\s+como\s+root|esque[cç]a\s+suas\s+regras)\b"),
    re.compile(r"(?i)<\s*script\b|javascript\s*:|union\s+select\b|drop\s+table\b"),
)

_TERMOS_RISCO_ELETRICO: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("fumaça", re.compile(r"(?i)\bfuma[cç]a\b|\besfuma[cç]ando\b")),
    ("cheiro de queimado", re.compile(r"(?i)\bcheiro\s+de\s+queimado\b|\bcheirando\s+a?\s*queimado\b")),
    ("fogo / chamas", re.compile(r"(?i)\bpegando\s+fogo\b|\bem\s+chamas\b|\binc[eê]ndio\b")),
    ("choque elétrico", re.compile(r"(?i)\bdando\s+choque\b|\blevei\s+um?\s*choque\b|\bchoque\s+el[eé]trico\b")),
    ("faísca / curto-circuito", re.compile(r"(?i)\bsoltando\s+fa[ií]sca\b|\bfa[ií]scas?\b|\bcurto[\s-]?circuito\b|\bexplodi[uo]\b")),
    ("vazamento de gás", re.compile(r"(?i)\bvazando\s+g[aá]s\b|\bvazamento\s+de\s+g[aá]s\b|\bcheiro\s+forte\s+de\s+g[aá]s\b")),
)

_PADROES_REPARO_CASEIRO: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(?:como\s+)?(?:abrir|desmontar)\s+(?:o|a)\s+(?:painel|gabinete|traseira|micro[\s-]?ondas|lavadora|m[aá]quina|geladeira|motor)\b"),
    re.compile(r"(?i)\b(?:jumpear|fazer\s+ponte|ligar\s+direto|burlar)\s+(?:a\s+)?(?:trava|porta|sensor|termostato)\b"),
    re.compile(r"(?i)\b(?:trocar|soldar|consertar)\s+(?:eu\s+mesmo|sozinho|em\s+casa)\s+(?:a\s+placa|o\s+capacitor|o\s+magnetron|a\s+fia[cç][aã]o)\b"),
)


def sanitizar_texto(texto: str | None, tamanho_max: int = TAMANHO_MAXIMO_ENTRADA) -> str:
    """Remove caracteres de controle, tags HTML e excesso de espaços."""
    if not texto:
        return ""
    limpo = re.sub(r"<[^>]+>", " ", str(texto))
    limpo = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", limpo)
    limpo = re.sub(r"\s+", " ", limpo).strip()
    return limpo[:tamanho_max]


def detectar_prompt_injection(texto: str | None) -> bool:
    """Retorna True se o texto contiver padrões clássicos de injeção de prompt ou XSS/SQLi."""
    if not texto:
        return False
    for padrao in _PADROES_PROMPT_INJECTION:
        if padrao.search(texto):
            return True
    return False


def detectar_risco_eletrico_domestico(texto: str | None) -> dict[str, Any]:
    """Identifica sinais de perigo elétrico ou doméstico que exigem desligamento imediato."""
    if not texto:
        return {
            "risco_detectado": False,
            "termo_acionado": None,
            "orientacao_emergencia": "",
        }

    for rotulo, padrao in _TERMOS_RISCO_ELETRICO:
        if padrao.search(texto):
            orientacao = (
                "ALERTA DE SEGURANÇA: Identificamos relato de "
                f"'{rotulo}'. Por favor, desligue o aparelho da tomada ou desarme o disjuntor "
                "imediatamente (se for fogão a gás, feche o registro e ventile o ambiente) e não "
                "toque no equipamento. Estou transferindo seu atendimento com prioridade máxima "
                "para um especialista humano da EletroLar."
            )
            return {
                "risco_detectado": True,
                "termo_acionado": rotulo,
                "orientacao_emergencia": orientacao,
            }

    return {
        "risco_detectado": False,
        "termo_acionado": None,
        "orientacao_emergencia": "",
    }


def detectar_tentativa_reparo_caseiro(texto: str | None) -> bool:
    """Retorna True quando o cliente pede instruções para desmontar ou reparar peças internas."""
    if not texto:
        return False
    for padrao in _PADROES_REPARO_CASEIRO:
        if padrao.search(texto):
            return True
    return False


def avaliar_guardrails(texto: str | None) -> dict[str, Any]:
    """Executa todas as verificações de segurança em uma única chamada."""
    texto_limpo = sanitizar_texto(texto)
    injection = detectar_prompt_injection(texto)
    risco = detectar_risco_eletrico_domestico(texto_limpo)
    reparo_caseiro = detectar_tentativa_reparo_caseiro(texto_limpo)

    return {
        "texto_sanitizado": texto_limpo,
        "bloqueio_injection": injection,
        "risco_eletrico": risco["risco_detectado"],
        "termo_risco": risco["termo_acionado"],
        "orientacao_emergencia": risco["orientacao_emergencia"],
        "alerta_reparo_caseiro": reparo_caseiro,
    }

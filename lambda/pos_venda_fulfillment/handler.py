"""Handler AWS Lambda (Python 3.12) para o Bot Amazon Lex V2 do Pós-Venda EletroLar Varejo.

Suporta:
- `DialogCodeHook` (validação progressiva e elicitação amigável de slots)
- `FulfillmentCodeHook` (execução das 3 jornadas principais do PDF + Transbordo N1)
- Preservação integral de contexto nos atributos de sessão `pv_*` para exibição no
  Agent Workspace / Contact Control Panel (CCP v2) do Amazon Connect.
"""

from __future__ import annotations

from typing import Any

from assistencia import (
    buscar_assistencia_mais_proxima,
    extrair_cep,
    normalizar_categoria,
)
from garantia_troca import (
    gerar_protocolo_deterministico,
    normalizar_nota_fiscal,
    normalizar_numero_serie,
    processar_acionamento_garantia,
    processar_troca_devolucao,
)
from guardrails import avaliar_guardrails
from respostas import (
    formatar_aviso_reparo_caseiro,
    formatar_resposta_assistencia,
    formatar_resposta_garantia,
    formatar_resposta_troca,
)

SLOTS_GARANTIA: tuple[tuple[str, str], ...] = (
    ("ModeloProduto", "Qual é o modelo ou tipo do eletrodoméstico que apresentou defeito (por exemplo: Lavadora 12kg, Geladeira FrostFree ou Micro-ondas 32L)?"),
    ("NumeroSerie", "Por favor, informe o número de série do aparelho (ex.: EL-LAV-2026-8841), localizado na etiqueta traseira ou lateral."),
    ("NumeroNotaFiscal", "Qual é o número da sua Nota Fiscal de compra (ex.: NF-100201)?"),
    ("DescricaoDefeito", "Pode descrever brevemente o que está acontecendo com o produto (ex.: parou de funcionar, não centrifuga, não gela)?"),
)

SLOTS_ASSISTENCIA: tuple[tuple[str, str], ...] = (
    ("CepOuCidade", "Por favor, informe o seu CEP (8 dígitos) ou o nome da sua cidade para eu localizar a assistência técnica autorizada mais próxima."),
)

SLOTS_TROCA: tuple[tuple[str, str], ...] = (
    ("NumeroNotaFiscal", "Para iniciar a troca ou devolução, informe o número da sua Nota Fiscal (ex.: NF-100203)."),
    ("ModeloProduto", "Qual é o modelo do produto que você deseja trocar ou devolver?"),
    ("MotivoSolicitacao", "Qual é o motivo da troca ou devolução (ex.: arrependimento em até 7 dias, produto avariado na entrega ou defeito)?"),
)


def _obter_valor_slot(slots: dict[str, Any], nome: str) -> str | None:
    """Extrai o valor interpretado ou original de um slot do Amazon Lex V2."""
    slot_obj = slots.get(nome)
    if not slot_obj or not isinstance(slot_obj, dict):
        return None
    val = slot_obj.get("value")
    if isinstance(val, dict):
        interpretado = val.get("interpretedValue") or val.get("originalValue")
        if interpretado and str(interpretado).strip():
            return str(interpretado).strip()
    return None


def _definir_slot(slots: dict[str, Any], nome: str, valor: str) -> None:
    """Preenche um slot no formato esperado pelo Amazon Lex V2."""
    slots[nome] = {
        "shape": "Scalar",
        "value": {
            "originalValue": valor,
            "interpretedValue": valor,
            "resolvedValues": [valor],
        },
    }


def _resposta_lex(
    intent_name: str,
    slots: dict[str, Any],
    session_attributes: dict[str, str],
    mensagem: str,
    dialog_action_type: str = "Close",
    fulfillment_state: str = "Fulfilled",
    slot_to_elicit: str | None = None,
) -> dict[str, Any]:
    """Constrói o envelope oficial de resposta do Amazon Lex V2."""
    dialog_action: dict[str, Any] = {"type": dialog_action_type}
    if dialog_action_type == "ElicitSlot" and slot_to_elicit:
        dialog_action["slotToElicit"] = slot_to_elicit

    intent_state = "InProgress" if dialog_action_type == "ElicitSlot" else fulfillment_state

    return {
        "sessionState": {
            "dialogAction": dialog_action,
            "intent": {
                "name": intent_name,
                "slots": slots,
                "state": intent_state,
            },
            "sessionAttributes": {k: str(v) for k, v in session_attributes.items() if v is not None},
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": mensagem,
            }
        ],
    }


def _montar_resumo_agente(attrs: dict[str, str]) -> str:
    """Gera o atributo `pv_resumo` conciso para leitura imediata no CCP v2 / Agent Workspace."""
    partes = [
        f"Jornada={attrs.get('pv_jornada', 'N/A')}",
        f"Protocolo={attrs.get('pv_protocolo', 'N/A')}",
    ]
    if attrs.get("pv_nota_fiscal"):
        partes.append(f"NF={attrs['pv_nota_fiscal']}")
    if attrs.get("pv_modelo"):
        partes.append(f"Produto={attrs['pv_modelo']}")
    if attrs.get("pv_numero_serie"):
        partes.append(f"Serie={attrs['pv_numero_serie']}")
    if attrs.get("pv_status_garantia"):
        partes.append(f"Garantia={attrs['pv_status_garantia']}")
    if attrs.get("pv_cep_cidade"):
        partes.append(f"Local={attrs['pv_cep_cidade']}")
    if attrs.get("pv_motivo_transbordo") and attrs.get("pv_motivo_transbordo") != "NENHUM":
        partes.append(f"Transbordo={attrs['pv_motivo_transbordo']}")
    return " | ".join(partes)


def _enriquecer_slots_por_transcript(intent_name: str, slots: dict[str, Any], transcript: str) -> None:
    """Extrai automaticamente NF, Série, CEP e Categoria caso o cliente já os tenha informado na frase."""
    if not transcript:
        return

    nf_Auto = normalizar_nota_fiscal(transcript)
    if nf_Auto and intent_name in {"AcionarGarantiaDefeito", "SolicitarTrocaDevolucao"}:
        if not _obter_valor_slot(slots, "NumeroNotaFiscal"):
            _definir_slot(slots, "NumeroNotaFiscal", nf_Auto)

    serie_auto = normalizar_numero_serie(transcript)
    if serie_auto and intent_name == "AcionarGarantiaDefeito":
        if not _obter_valor_slot(slots, "NumeroSerie"):
            _definir_slot(slots, "NumeroSerie", serie_auto)

    cat_auto = normalizar_categoria(transcript)
    if cat_auto and intent_name == "LocalizarAssistenciaTecnica":
        if not _obter_valor_slot(slots, "CategoriaProduto"):
            _definir_slot(slots, "CategoriaProduto", cat_auto)

    cep_auto = extrair_cep(transcript)
    if cep_auto and intent_name == "LocalizarAssistenciaTecnica":
        if not _obter_valor_slot(slots, "CepOuCidade"):
            _definir_slot(slots, "CepOuCidade", cep_auto)


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Entrypoint principal da AWS Lambda para o Amazon Lex V2."""
    session_state = event.get("sessionState") or {}
    session_attrs: dict[str, str] = dict(session_state.get("sessionAttributes") or {})
    intent = session_state.get("intent") or {}
    intent_name = intent.get("name", "FallbackIntent")
    slots: dict[str, Any] = dict(intent.get("slots") or {})
    invocation_source = event.get("invocationSource", "FulfillmentCodeHook")
    transcript = str(event.get("inputTranscript") or "")

    canal = session_attrs.get("pv_canal", "CHAT").upper()
    session_attrs["pv_canal"] = canal
    session_attrs.setdefault("pv_risco_seguranca", "FALSE")
    session_attrs.setdefault("pv_transbordo", "FALSE")
    session_attrs.setdefault("pv_motivo_transbordo", "NENHUM")

    # 1. Avaliação da camada de Guardrails sobre a fala do cliente e slots preenchidos
    textos_avaliacao = [transcript] + [
        _obter_valor_slot(slots, k) or "" for k in slots
    ]
    texto_consolidado = " ".join(t for t in textos_avaliacao if t).strip()
    analise_seg = avaliar_guardrails(texto_consolidado)

    if analise_seg["bloqueio_injection"]:
        session_attrs["pv_jornada"] = "BLOQUEIO_GUARDRAIL"
        session_attrs["pv_transbordo"] = "FALSE"
        session_attrs["pv_motivo_transbordo"] = "TENTATIVA_INJECAO_BLOQUEADA"
        session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
        return _resposta_lex(
            intent_name=intent_name,
            slots={},
            session_attributes=session_attrs,
            mensagem=(
                "Por motivos de segurança, não pude processar essa instrução. "
                "Posso ajudar você com: 1) Defeito e acionamento de garantia, "
                "2) Localização de assistência técnica autorizada por CEP/cidade, ou "
                "3) Solicitação de troca ou devolução."
            ),
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    if analise_seg["risco_eletrico"]:
        proto_emergencia = gerar_protocolo_deterministico(
            "EMERGENCIA", analise_seg["termo_risco"] or "RISCO_ELETRICO"
        )
        session_attrs["pv_jornada"] = "EMERGENCIA_SEGURANCA"
        session_attrs["pv_risco_seguranca"] = "TRUE"
        session_attrs["pv_transbordo"] = "TRUE"
        session_attrs["pv_motivo_transbordo"] = "ALERTA_SEGURANCA_ELETRICA"
        session_attrs["pv_protocolo"] = proto_emergencia
        session_attrs["pv_defeito_relatado"] = analise_seg["texto_sanitizado"][:180]
        session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
        return _resposta_lex(
            intent_name=intent_name,
            slots=slots,
            session_attributes=session_attrs,
            mensagem=f"{analise_seg['orientacao_emergencia']} (Protocolo prioritário: {proto_emergencia}).",
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    if analise_seg["alerta_reparo_caseiro"]:
        session_attrs["pv_jornada"] = "PREVENCAO_REPARO_CASEIRO"
        session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
        return _resposta_lex(
            intent_name=intent_name,
            slots=slots,
            session_attributes=session_attrs,
            mensagem=formatar_aviso_reparo_caseiro(),
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    # Enriquecimento inteligente de slots a partir da frase natural
    _enriquecer_slots_por_transcript(intent_name, slots, analise_seg["texto_sanitizado"])

    # 2. Intenção: FalarComAtendente ou FallbackIntent
    if intent_name == "FalarComAtendente":
        proto = session_attrs.get("pv_protocolo") or gerar_protocolo_deterministico(
            "ATENDENTE", session_attrs.get("pv_nota_fiscal", "HUMANO")
        )
        session_attrs["pv_jornada"] = session_attrs.get("pv_jornada") or "ATENDIMENTO_HUMANO"
        session_attrs["pv_protocolo"] = proto
        session_attrs["pv_transbordo"] = "TRUE"
        session_attrs["pv_motivo_transbordo"] = "SOLICITACAO_CLIENTE"
        session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
        return _resposta_lex(
            intent_name=intent_name,
            slots=slots,
            session_attributes=session_attrs,
            mensagem=(
                f"Com certeza! Estou transferindo seu atendimento agora para um especialista da EletroLar "
                f"(Protocolo {proto}). Todas as informações e o histórico da nossa conversa já foram "
                f"encaminhados para que você não precise repetir nada."
            ),
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    if intent_name == "FallbackIntent":
        tentativas = int(session_attrs.get("pv_tentativas_fallback", "0")) + 1
        session_attrs["pv_tentativas_fallback"] = str(tentativas)
        if tentativas >= 2:
            proto = gerar_protocolo_deterministico("FALLBACK", str(tentativas))
            session_attrs["pv_jornada"] = session_attrs.get("pv_jornada") or "ATENDIMENTO_HUMANO"
            session_attrs["pv_protocolo"] = proto
            session_attrs["pv_transbordo"] = "TRUE"
            session_attrs["pv_motivo_transbordo"] = "FALLBACK_EXCEDIDO"
            session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
            return _resposta_lex(
                intent_name=intent_name,
                slots=slots,
                session_attributes=session_attrs,
                mensagem=(
                    f"Quero garantir que você seja atendido da melhor forma. Vou transferir nossa conversa "
                    f"para um especialista humano da EletroLar (Protocolo {proto}) com todo o histórico preservado."
                ),
                dialog_action_type="Close",
                fulfillment_state="Fulfilled",
            )
        return _resposta_lex(
            intent_name=intent_name,
            slots=slots,
            session_attributes=session_attrs,
            mensagem=(
                "Olá! Sou a assistente virtual de Pós-Venda da EletroLar. Posso ajudar você com:\n"
                "1) Defeito no produto e acionamento de garantia;\n"
                "2) Localizar assistência técnica autorizada (por CEP ou cidade);\n"
                "3) Solicitar troca ou devolução.\n"
                "Como posso ajudar hoje?"
            ),
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    # 3. Cenário 1: AcionarGarantiaDefeito
    if intent_name == "AcionarGarantiaDefeito":
        session_attrs["pv_jornada"] = "DEFEITO_GARANTIA"
        for nome_slot, pergunta in SLOTS_GARANTIA:
            valor = _obter_valor_slot(slots, nome_slot)
            if not valor:
                if invocation_source == "DialogCodeHook":
                    session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
                    return _resposta_lex(
                        intent_name=intent_name,
                        slots=slots,
                        session_attributes=session_attrs,
                        mensagem=pergunta,
                        dialog_action_type="ElicitSlot",
                        slot_to_elicit=nome_slot,
                    )
                # Em invocação direta de Fulfillment sem algum slot, solicita o slot faltante
                return _resposta_lex(
                    intent_name=intent_name,
                    slots=slots,
                    session_attributes=session_attrs,
                    mensagem=pergunta,
                    dialog_action_type="ElicitSlot",
                    slot_to_elicit=nome_slot,
                )

        modelo = _obter_valor_slot(slots, "ModeloProduto") or ""
        serie = _obter_valor_slot(slots, "NumeroSerie") or ""
        nf = _obter_valor_slot(slots, "NumeroNotaFiscal") or ""
        defeito = _obter_valor_slot(slots, "DescricaoDefeito") or ""

        resultado = processar_acionamento_garantia(
            modelo_produto=modelo,
            numero_serie=serie,
            nota_fiscal=nf,
            descricao_defeito=defeito,
        )

        session_attrs["pv_modelo"] = str(resultado["modelo_produto"])
        session_attrs["pv_categoria"] = str(resultado["categoria_produto"])
        session_attrs["pv_numero_serie"] = str(resultado["numero_serie"])
        session_attrs["pv_nota_fiscal"] = str(resultado["nota_fiscal"])
        session_attrs["pv_defeito_relatado"] = str(resultado["descricao_defeito"])
        session_attrs["pv_status_garantia"] = str(resultado["status_garantia"])
        session_attrs["pv_protocolo"] = str(resultado["protocolo"])
        session_attrs["pv_transbordo"] = "TRUE" if resultado["transbordo"] else "FALSE"
        session_attrs["pv_motivo_transbordo"] = str(resultado["motivo_transbordo"] or "NENHUM")

        ast_vinc = resultado.get("assistencia_vinculada")
        if ast_vinc:
            session_attrs["pv_assistencia_nome"] = str(ast_vinc.get("nome_fantasia", ""))
            session_attrs["pv_assistencia_contato"] = (
                f"{ast_vinc.get('endereco', '')} | {ast_vinc.get('telefone', '')} | {ast_vinc.get('horario_atendimento', '')}"
            )

        session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
        msg = formatar_resposta_garantia(resultado, canal=canal)
        return _resposta_lex(
            intent_name=intent_name,
            slots=slots,
            session_attributes=session_attrs,
            mensagem=msg,
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    # 4. Cenário 2: LocalizarAssistenciaTecnica
    if intent_name == "LocalizarAssistenciaTecnica":
        session_attrs["pv_jornada"] = "LOCALIZAR_ASSISTENCIA"
        for nome_slot, pergunta in SLOTS_ASSISTENCIA:
            valor = _obter_valor_slot(slots, nome_slot)
            if not valor:
                return _resposta_lex(
                    intent_name=intent_name,
                    slots=slots,
                    session_attributes=session_attrs,
                    mensagem=pergunta,
                    dialog_action_type="ElicitSlot",
                    slot_to_elicit=nome_slot,
                )

        cep_ou_cidade = _obter_valor_slot(slots, "CepOuCidade") or ""
        categoria = _obter_valor_slot(slots, "CategoriaProduto")
        resultado_ast = buscar_assistencia_mais_proxima(
            cep_ou_cidade=cep_ou_cidade,
            categoria_produto=categoria,
        )

        session_attrs["pv_cep_cidade"] = str(resultado_ast["localidade_informada"])
        if resultado_ast.get("categoria_filtrada"):
            session_attrs["pv_categoria"] = str(resultado_ast["categoria_filtrada"])

        if resultado_ast["encontrada"] and resultado_ast["unidade_principal"]:
            u = resultado_ast["unidade_principal"]
            proto = gerar_protocolo_deterministico("AST", f"{cep_ou_cidade}:{u['id_unidade']}")
            session_attrs["pv_protocolo"] = proto
            session_attrs["pv_assistencia_nome"] = str(u["nome_fantasia"])
            session_attrs["pv_assistencia_contato"] = (
                f"{u['endereco']} | Tel: {u['telefone']} | Horário: {u['horario_atendimento']}"
            )
            session_attrs["pv_transbordo"] = "FALSE"
            session_attrs["pv_motivo_transbordo"] = "NENHUM"
        else:
            proto = gerar_protocolo_deterministico("AST-SEM-COB", cep_ou_cidade)
            session_attrs["pv_protocolo"] = proto
            session_attrs["pv_assistencia_nome"] = "SEM_COBERTURA_LOCAL"
            session_attrs["pv_transbordo"] = "TRUE"
            session_attrs["pv_motivo_transbordo"] = "CEP_SEM_ASSISTENCIA"

        session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
        msg = formatar_resposta_assistencia(resultado_ast, canal=canal)
        return _resposta_lex(
            intent_name=intent_name,
            slots=slots,
            session_attributes=session_attrs,
            mensagem=msg,
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    # 5. Cenário 3: SolicitarTrocaDevolucao
    if intent_name == "SolicitarTrocaDevolucao":
        session_attrs["pv_jornada"] = "TROCA_DEVOLUCAO"
        for nome_slot, pergunta in SLOTS_TROCA:
            valor = _obter_valor_slot(slots, nome_slot)
            if not valor:
                return _resposta_lex(
                    intent_name=intent_name,
                    slots=slots,
                    session_attributes=session_attrs,
                    mensagem=pergunta,
                    dialog_action_type="ElicitSlot",
                    slot_to_elicit=nome_slot,
                )

        nf = _obter_valor_slot(slots, "NumeroNotaFiscal") or ""
        modelo = _obter_valor_slot(slots, "ModeloProduto") or ""
        motivo = _obter_valor_slot(slots, "MotivoSolicitacao") or ""

        resultado_troca = processar_troca_devolucao(
            nota_fiscal=nf,
            modelo_produto=modelo,
            motivo_solicitacao=motivo,
        )

        session_attrs["pv_nota_fiscal"] = str(resultado_troca["nota_fiscal"])
        session_attrs["pv_modelo"] = str(resultado_troca["modelo_produto"])
        session_attrs["pv_categoria"] = str(resultado_troca["categoria_produto"])
        if resultado_troca.get("numero_serie"):
            session_attrs["pv_numero_serie"] = str(resultado_troca["numero_serie"])
        session_attrs["pv_motivo_troca"] = str(resultado_troca["motivo_solicitacao"])
        session_attrs["pv_elegibilidade_troca"] = str(resultado_troca["elegibilidade"])
        session_attrs["pv_protocolo"] = str(resultado_troca["protocolo"])
        session_attrs["pv_transbordo"] = "TRUE" if resultado_troca["transbordo"] else "FALSE"
        session_attrs["pv_motivo_transbordo"] = str(resultado_troca["motivo_transbordo"] or "NENHUM")

        session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
        msg = formatar_resposta_troca(resultado_troca, canal=canal)
        return _resposta_lex(
            intent_name=intent_name,
            slots=slots,
            session_attributes=session_attrs,
            mensagem=msg,
            dialog_action_type="Close",
            fulfillment_state="Fulfilled",
        )

    # Intenção desconhecida -> Fallback seguro
    session_attrs["pv_resumo"] = _montar_resumo_agente(session_attrs)
    return _resposta_lex(
        intent_name=intent_name,
        slots=slots,
        session_attributes=session_attrs,
        mensagem="Como posso ajudar você no Pós-Venda da EletroLar? Informe se precisa de garantia para defeito, endereço de assistência técnica ou troca/devolução.",
        dialog_action_type="Close",
        fulfillment_state="Fulfilled",
    )

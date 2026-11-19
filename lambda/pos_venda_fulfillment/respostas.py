"""Templates de respostas humanizadas e empáticas otimizadas para Chat Online e Voz (Amazon Polly Camila)."""

from __future__ import annotations

from typing import Any


def formatar_resposta_garantia(resultado: dict[str, Any], canal: str = "CHAT") -> str:
    """Formata a resposta do fluxo AcionarGarantiaDefeito (Cenário 1)."""
    eh_voz = canal.upper() == "VOICE"
    protocolo = resultado.get("protocolo", "PV-00000000-0000")
    modelo = resultado.get("modelo_produto", "eletrodoméstico")
    serie = resultado.get("numero_serie", "")
    nf = resultado.get("nota_fiscal", "")
    status = resultado.get("status_garantia", "")
    garantia_ate = resultado.get("garantia_ate", "")
    ast = resultado.get("assistencia_vinculada")

    if status == "ATIVA" and ast:
        if eh_voz:
            return (
                f"Perfeito! Localizei a nota fiscal {nf} do seu produto {modelo}, série {serie}. "
                f"Sua garantia está ativa até {garantia_ate}. Acionei o atendimento em garantia sob o "
                f"protocolo {protocolo}. A autorizada responsável é a {ast['nome_fantasia']}, "
                f"no telefone {ast['telefone']}, com funcionamento de {ast['horario_atendimento']}."
            )
        return (
            f"Garantia acionada automaticamente com sucesso!\n\n"
            f"• Protocolo de Garantia: {protocolo}\n"
            f"• Produto: {modelo} (Série: {serie})\n"
            f"• Nota Fiscal: {nf} — Garantia ATIVA até {garantia_ate}\n"
            f"• Assistência Autorizada Vinculada: {ast['nome_fantasia']}\n"
            f"• Endereço: {ast['endereco']}\n"
            f"• Telefone: {ast['telefone']}\n"
            f"• Horário: {ast['horario_atendimento']}\n"
            f"• Prazo de Visita / Atendimento: {ast.get('prazo_medio_visita', 'Até 48 horas úteis')}"
        )

    if status == "ATIVA" and not ast:
        return (
            f"Sua garantia para o produto {modelo} (Nota Fiscal {nf}, Série {serie}) está ATIVA até {garantia_ate} "
            f"e geramos o protocolo {protocolo}. Como não há posto autorizado presencial diretamente no seu CEP, "
            f"estou transferindo você agora para nosso especialista organizar a coleta domiciliar gratuita sem que "
            f"você precise repetir nenhum dado."
        )

    if status == "EXPIRADA":
        return (
            f"Verifiquei a Nota Fiscal {nf} referente ao produto {modelo} (Série {serie}) e identifiquei "
            f"que o período de garantia contratual encerrou em {garantia_ate}. Gerei o protocolo {protocolo} "
            f"e estou transferindo seu atendimento para um especialista da EletroLar apresentar opções "
            f"de reparo autorizado com condição especial. Todo o histórico já foi encaminhado."
        )

    return (
        f"Registrei os dados do seu produto {modelo} (Série {serie}, Nota Fiscal {nf}) sob o protocolo "
        f"{protocolo}. Não consegui validar a nota automaticamente na base instantânea, por isso "
        f"estou transferindo você para um especialista humano concluir o acionamento sem precisar repetir nada."
    )


def formatar_resposta_assistencia(resultado: dict[str, Any], canal: str = "CHAT") -> str:
    """Formata a resposta do fluxo LocalizarAssistenciaTecnica (Cenário 2)."""
    eh_voz = canal.upper() == "VOICE"
    localidade = resultado.get("localidade_informada", "sua região")
    unidade = resultado.get("unidade_principal")

    if not resultado.get("encontrada") or not unidade:
        return (
            f"Consultei nossa rede para a localidade '{localidade}', mas não encontramos uma assistência "
            f"técnica autorizada presencial diretamente nesse CEP ou município. Estou transferindo seu "
            f"atendimento para um especialista humano da EletroLar providenciar o atendimento itinerante "
            f"ou código de logística reversa gratuita, preservando todo o contexto da nossa conversa."
        )

    if eh_voz:
        return (
            f"Encontrei a assistência técnica autorizada mais próxima para {localidade}: "
            f"{unidade['nome_fantasia']}, localizada em {unidade['endereco']}. "
            f"O telefone é {unidade['telefone']} e o horário de atendimento é {unidade['horario_atendimento']}."
        )

    especialidades = ", ".join(unidade.get("especialidades", []))
    texto = (
        f"Localizei a assistência técnica autorizada mais próxima para {localidade}:\n\n"
        f"• Autorizada: {unidade['nome_fantasia']} ({unidade['id_unidade']})\n"
        f"• Endereço: {unidade['endereco']}\n"
        f"• Telefone: {unidade['telefone']}\n"
        f"• Horário de Atendimento: {unidade['horario_atendimento']}\n"
        f"• Especialidades: {especialidades}"
    )

    adicionais = resultado.get("unidades_adicionais") or []
    if adicionais:
        extra = adicionais[0]
        texto += (
            f"\n\nOpção adicional na mesma região:\n"
            f"• {extra['nome_fantasia']} — {extra['endereco']} | Tel: {extra['telefone']} ({extra['horario_atendimento']})"
        )
    return texto


def formatar_resposta_troca(resultado: dict[str, Any], canal: str = "CHAT") -> str:
    """Formata a resposta do fluxo SolicitarTrocaDevolucao (Cenário 3)."""
    eh_voz = canal.upper() == "VOICE"
    protocolo = resultado.get("protocolo", "PV-00000000-0000")
    nf = resultado.get("nota_fiscal", "")
    modelo = resultado.get("modelo_produto", "produto")
    motivo = resultado.get("motivo_solicitacao", "")
    elegibilidade = resultado.get("elegibilidade", "")

    if elegibilidade == "ELEGIVEL":
        if eh_voz:
            return (
                f"Sua solicitação de troca ou devolução para o produto {modelo}, nota fiscal {nf}, "
                f"foi aberta com sucesso sob o protocolo {protocolo}. Enviamos os detalhes da coleta "
                f"domiciliar gratuita e o comprovante do protocolo no chat."
            )
        return (
            f"Solicitação de Troca / Devolução registrada com sucesso!\n\n"
            f"• Protocolo Oficial: {protocolo}\n"
            f"• Nota Fiscal: {nf}\n"
            f"• Produto: {modelo}\n"
            f"• Motivo Registrado: {motivo}\n"
            f"• Status: ELEGÍVEL (Dentro do prazo legal — Coleta reversa domiciliar autorizada)\n"
            f"• Próximo Passo: Guarde este protocolo ({protocolo}). Nossa equipe logística realizará a coleta em até 48h úteis."
        )

    motivo_bloq = resultado.get("motivo_bloqueio") or "Necessária validação complementar pela equipe N1."
    return (
        f"Registrei seu pedido de troca/devolução para o produto {modelo} (Nota Fiscal {nf}) e gerei "
        f"o protocolo {protocolo}. Observação do sistema: {motivo_bloq} "
        f"Estou transferindo seu atendimento agora para um especialista humano da EletroLar avaliar "
        f"a melhor solução com todo o histórico desta conversa já disponível na tela."
    )


def formatar_aviso_reparo_caseiro() -> str:
    """Mensagem preventiva contra tentativa de reparo caseiro que invalida a garantia."""
    return (
        "Importante: Para sua segurança contra choques elétricos e para **não invalidar sua garantia "
        "de 12 meses**, nunca abra o gabinete, painel ou componentes internos do eletrodoméstico. "
        "Informe o modelo, número de série e nota fiscal para acionarmos a garantia oficial, "
        "ou informe seu CEP/cidade para localizarmos a assistência técnica autorizada mais próxima."
    )

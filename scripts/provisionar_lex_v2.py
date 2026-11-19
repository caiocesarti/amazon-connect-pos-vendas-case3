#!/usr/bin/env python3
"""Provisiona automaticamente o Bot Amazon Lex V2 `PV-EletroLar-Bot` (pt_BR, Camila Neural) na AWS.

Cria ou atualiza:
1. IAM Role do Lex V2 (`PV-LexV2BotRole`) e permissão `lambda:InvokeFunction` na Lambda `PV-PosVendaFulfillment`
2. Bot `PV-EletroLar-Bot` + Locale `pt_BR` (Voz Neural `Camila`, threshold `0.40`)
3. Slot Types customizados (`PV_CategoriaEletrodomestico` e `PV_MotivoTrocaDevolucao`)
4. Intenções (`AcionarGarantiaDefeito`, `LocalizarAssistenciaTecnica`, `SolicitarTrocaDevolucao`,
   `FalarComAtendente` e `FallbackIntent`) com slots e sample utterances
5. Build do locale `pt_BR`, criação de versão e associação do Alias `Prod` (e `TestBotAlias`) à Lambda.

Uso (no AWS CloudShell ou terminal autenticado):
    python3 scripts/provisionar_lex_v2.py --region us-west-2
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError


def obter_ou_criar_role_lex(iam_client: Any, nome_role: str = "PV-LexV2BotRole") -> str:
    try:
        resp = iam_client.get_role(RoleName=nome_role)
        return str(resp["Role"]["Arn"])
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "NoSuchEntity":
            raise

    print(f"[1/7] Criando IAM Role {nome_role} para o Amazon Lex V2...")
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lexv2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    resp = iam_client.create_role(
        RoleName=nome_role,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Role de execucao do bot Amazon Lex V2 PV-EletroLar-Bot",
    )
    iam_client.put_role_policy(
        RoleName=nome_role,
        PolicyName="PV-LexPollyPolicy",
        PolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["polly:SynthesizeSpeech"],
                        "Resource": "*",
                    }
                ],
            }
        ),
    )
    print("      Aguardando propagação da Role IAM (8s)...")
    time.sleep(8)
    return str(resp["Role"]["Arn"])


def autorizar_lex_na_lambda(lambda_client: Any, nome_funcao: str, account_id: str, regiao: str) -> str:
    resp = lambda_client.get_function(FunctionName=nome_funcao)
    lambda_arn = str(resp["Configuration"]["FunctionArn"])
    try:
        lambda_client.add_permission(
            FunctionName=nome_funcao,
            StatementId="PermitirInvocacaoAmazonLexV2PosVenda",
            Action="lambda:InvokeFunction",
            Principal="lexv2.amazonaws.com",
            SourceArn=f"arn:aws:lex:{regiao}:{account_id}:bot-alias/*",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceConflictException":
            raise
    return lambda_arn


def aguardar_status(fn_describe: Any, chave_status: str, status_alvo: set[str], **kwargs: Any) -> dict[str, Any]:
    for _ in range(60):
        try:
            resp = fn_describe(**kwargs)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ResourceNotFoundException":
                time.sleep(3)
                continue
            raise
        atual = resp.get(chave_status, "")
        if atual in status_alvo:
            return dict(resp)
        if atual in {"Failed", "Deleting"}:
            raise RuntimeError(f"Erro no recurso Lex ({chave_status}={atual}): {resp.get('failureReasons')}")
        time.sleep(3)
    raise TimeoutError(f"Timeout aguardando {chave_status} atingir {status_alvo}")


def provisionar_bot_lex(regiao: str = "us-west-2", nome_lambda: str = "PV-PosVendaFulfillment") -> None:
    sts = boto3.client("sts", region_name=regiao)
    iam = boto3.client("iam", region_name=regiao)
    lmb = boto3.client("lambda", region_name=regiao)
    lex = boto3.client("lexv2-models", region_name=regiao)

    account_id = sts.get_caller_identity()["Account"]
    role_arn = obter_ou_criar_role_lex(iam)
    print(f"[2/7] Vinculando permissão na Lambda {nome_lambda}...")
    lambda_arn = autorizar_lex_na_lambda(lmb, nome_lambda, account_id, regiao)

    # 1. Bot PV-EletroLar-Bot
    nome_bot = "PV-EletroLar-Bot"
    bots = lex.list_bots(
        filters=[{"name": "BotName", "values": [nome_bot], "operator": "EQ"}]
    ).get("botSummaries", [])

    if bots:
        bot_id = bots[0]["botId"]
        print(f"[3/7] Bot {nome_bot} já existe (botId={bot_id}). Atualizando definição...")
    else:
        print(f"[3/7] Criando Bot {nome_bot}...")
        criado = lex.create_bot(
            botName=nome_bot,
            roleArn=role_arn,
            dataPrivacy={"childDirected": False},
            idleSessionTTLInSeconds=300,
        )
        bot_id = criado["botId"]
        aguardar_status(lex.describe_bot, "botStatus", {"Available"}, botId=bot_id)

    # 2. Locale pt_BR (Camila Neural)
    locales = lex.list_bot_locales(botId=bot_id, botVersion="DRAFT").get("botLocaleSummaries", [])
    if not any(loc["localeId"] == "pt_BR" for loc in locales):
        print("[4/7] Criando idioma pt_BR com voz neural Camila...")
        lex.create_bot_locale(
            botId=bot_id,
            botVersion="DRAFT",
            localeId="pt_BR",
            nluIntentConfidenceThreshold=0.40,
            voiceSettings={"voiceId": "Camila", "engine": "neural"},
        )
    aguardar_status(
        lex.describe_bot_locale,
        "botLocaleStatus",
        {"NotBuilt", "Built", "ReadyExpressTesting"},
        botId=bot_id,
        botVersion="DRAFT",
        localeId="pt_BR",
    )

    # 3. Slot Types Customizados
    print("[5/7] Configurando Slot Types customizados...")
    slot_types_def = {
        "PV_CategoriaEletrodomestico": [
            ("LAVADORA", ["máquina de lavar", "lavadora de roupas", "lava e seca", "tanquinho", "centrífuga"]),
            ("GELADEIRA", ["geladeira", "refrigerador", "frost free", "geladeira inverse", "freezer"]),
            ("MICROONDAS", ["micro-ondas", "microondas", "forno de micro-ondas"]),
            ("FOGAO", ["fogão", "fogao 5 bocas", "fogao mesa de vidro", "cooktop"]),
            ("AR_CONDICIONADO", ["ar-condicionado", "ar condicionado split", "split inverter", "climatizador"]),
        ],
        "PV_MotivoTrocaDevolucao": [
            ("Arrependimento 7 dias", ["arrependimento", "desisti da compra", "quero devolver dentro dos 7 dias"]),
            ("Produto avariado na entrega", ["veio amassado", "chegou riscado", "avaria no transporte"]),
            ("Defeito funcional nos primeiros dias", ["veio com defeito", "parou de funcionar na primeira semana"]),
            ("Voltagem ou modelo divergente", ["voltagem errada", "entregaram modelo errado"]),
        ],
        "PV_ModeloEletrodomestico": [
            ("Lavadora 12kg", []),
            ("Lava e Seca 11kg", []),
            ("Geladeira FrostFree", []),
            ("Geladeira Inverse", []),
            ("Micro-ondas 32L", []),
            ("Fogão 5 Bocas", []),
            ("Ar-Condicionado Split", []),
        ],
        "PV_LocalidadeCepCidade": [
            ("01310-200", []),
            ("04029-200", []),
            ("41820-020", []),
            ("69900-000", []),
            ("São Paulo", []),
            ("Osasco", []),
            ("Campinas", []),
            ("Salvador", []),
            ("Lauro de Freitas", []),
            ("Feira de Santana", []),
            ("Rio de Janeiro", []),
            ("Belo Horizonte", []),
            ("Curitiba", []),
            ("Porto Alegre", []),
            ("Brasília", []),
        ],
    }

    existentes_st = {
        s["slotTypeName"]: s["slotTypeId"]
        for s in lex.list_slot_types(botId=bot_id, botVersion="DRAFT", localeId="pt_BR").get("slotTypeSummaries", [])
    }
    mapa_st_ids: dict[str, str] = {}

    for st_nome, valores in slot_types_def.items():
        estrategia = "OriginalValue" if st_nome in {"PV_ModeloEletrodomestico", "PV_LocalidadeCepCidade"} else "TopResolution"
        st_values = [
            (
                {"sampleValue": {"value": val}, "synonyms": [{"value": sin} for sin in sinonimos]}
                if sinonimos
                else {"sampleValue": {"value": val}}
            )
            for val, sinonimos in valores
        ]
        if st_nome in existentes_st:
            st_id = existentes_st[st_nome]
            lex.update_slot_type(
                botId=bot_id,
                botVersion="DRAFT",
                localeId="pt_BR",
                slotTypeId=st_id,
                slotTypeName=st_nome,
                slotTypeValues=st_values,
                valueSelectionSetting={"resolutionStrategy": estrategia},
            )
        else:
            resp_st = lex.create_slot_type(
                botId=bot_id,
                botVersion="DRAFT",
                localeId="pt_BR",
                slotTypeName=st_nome,
                slotTypeValues=st_values,
                valueSelectionSetting={"resolutionStrategy": estrategia},
            )
            st_id = resp_st["slotTypeId"]
        mapa_st_ids[st_nome] = st_id

    # 4. Intenções e Slots
    print("[6/7] Configurando as Intenções e Slots das 3 jornadas + Transbordo...")
    intents_def = [
        {
            "name": "AcionarGarantiaDefeito",
            "dialog": True,
            "utterances": [
                "minha máquina de lavar parou de funcionar",
                "a lavadora parou de funcionar e quero acionar a garantia",
                "meu produto está com defeito",
                "quero acionar a garantia do meu eletrodoméstico",
                "minha geladeira não está gelando",
                "meu micro-ondas não esquenta mais",
                "a máquina de lavar {ModeloProduto} parou de funcionar",
                "acionar garantia da nota fiscal {NumeroNotaFiscal}",
                "defeito no produto {ModeloProduto} série {NumeroSerie} nota {NumeroNotaFiscal}",
                "minha lava e seca apresentou erro no painel",
            ],
            "slots": [
                ("ModeloProduto", mapa_st_ids["PV_ModeloEletrodomestico"], "Required", "Qual é o modelo ou tipo do eletrodoméstico com defeito (ex.: Lavadora 12kg, Geladeira FrostFree)?"),
                ("NumeroSerie", "AMAZON.AlphaNumeric", "Required", "Informe o número de série do aparelho (ex.: EL-LAV-2026-8841)."),
                ("NumeroNotaFiscal", "AMAZON.AlphaNumeric", "Required", "Qual é o número da sua Nota Fiscal (ex.: NF-100201)?"),
                ("DescricaoDefeito", "AMAZON.FreeFormInput", "Required", "Descreva brevemente o defeito apresentado pelo aparelho."),
            ],
        },
        {
            "name": "LocalizarAssistenciaTecnica",
            "dialog": True,
            "utterances": [
                "quero localizar uma assistência técnica autorizada",
                "qual a assistência técnica mais próxima de mim",
                "buscar assistência autorizada no cep {CepOuCidade}",
                "assistência técnica em {CepOuCidade}",
                "onde tem autorizada para {CategoriaProduto} em {CepOuCidade}",
                "endereço e telefone da assistência em {CepOuCidade}",
                "posto autorizado perto do meu cep",
                "quero assistência técnica para minha máquina de lavar",
            ],
            "slots": [
                ("CepOuCidade", mapa_st_ids["PV_LocalidadeCepCidade"], "Required", "Por favor, informe o seu CEP (8 dígitos) ou o nome da sua cidade."),
                ("CategoriaProduto", mapa_st_ids["PV_CategoriaEletrodomestico"], "Optional", "Para qual linha de produto você busca assistência?"),
            ],
        },
        {
            "name": "SolicitarTrocaDevolucao",
            "dialog": True,
            "utterances": [
                "quero trocar meu produto",
                "preciso devolver um eletrodoméstico que comprei",
                "solicitar troca ou devolução",
                "quero devolver o produto da nota {NumeroNotaFiscal}",
                "trocar {ModeloProduto} da nota fiscal {NumeroNotaFiscal}",
                "meu produto chegou amassado e quero trocar",
                "direito de arrependimento 7 dias quero devolver",
            ],
            "slots": [
                ("NumeroNotaFiscal", "AMAZON.AlphaNumeric", "Required", "Informe o número da sua Nota Fiscal (ex.: NF-100203)."),
                ("ModeloProduto", mapa_st_ids["PV_ModeloEletrodomestico"], "Required", "Qual é o modelo do eletrodoméstico que deseja trocar ou devolver?"),
                ("MotivoSolicitacao", mapa_st_ids["PV_MotivoTrocaDevolucao"], "Required", "Qual é o motivo da troca ou devolução (ex.: arrependimento 7 dias ou avaria)?"),
            ],
        },
        {
            "name": "FalarComAtendente",
            "dialog": False,
            "utterances": [
                "quero falar com um atendente",
                "falar com humano",
                "transferir para especialista",
                "atendente humano por favor",
                "preciso falar com uma pessoa",
            ],
            "slots": [],
        },
    ]

    existentes_int = {
        i["intentName"]: i["intentId"]
        for i in lex.list_intents(botId=bot_id, botVersion="DRAFT", localeId="pt_BR").get("intentSummaries", [])
    }

    for idef in intents_def:
        iname = idef["name"]
        utts = [{"utterance": u} for u in idef["utterances"]]
        if iname in existentes_int:
            intent_id = existentes_int[iname]
        else:
            criado_i = lex.create_intent(
                botId=bot_id,
                botVersion="DRAFT",
                localeId="pt_BR",
                intentName=iname,
                sampleUtterances=[],
                dialogCodeHook={"enabled": idef["dialog"]},
                fulfillmentCodeHook={"enabled": True},
            )
            intent_id = criado_i["intentId"]

        slots_existentes = {
            s["slotName"]: s["slotId"]
            for s in lex.list_slots(
                botId=bot_id, botVersion="DRAFT", localeId="pt_BR", intentId=intent_id
            ).get("slotSummaries", [])
        }
        prioridades = []
        for idx, (sname, stype_id, constraint, prompt_txt) in enumerate(idef["slots"], start=1):
            elicitation = {
                "slotConstraint": constraint,
                "promptSpecification": {
                    "maxRetries": 2,
                    "messageGroups": [{"message": {"plainTextMessage": {"value": prompt_txt}}}],
                },
            }
            if sname in slots_existentes:
                sid = slots_existentes[sname]
                lex.update_slot(
                    botId=bot_id,
                    botVersion="DRAFT",
                    localeId="pt_BR",
                    intentId=intent_id,
                    slotId=sid,
                    slotName=sname,
                    slotTypeId=stype_id,
                    valueElicitationSetting=elicitation,
                )
            else:
                criado_s = lex.create_slot(
                    botId=bot_id,
                    botVersion="DRAFT",
                    localeId="pt_BR",
                    intentId=intent_id,
                    slotName=sname,
                    slotTypeId=stype_id,
                    valueElicitationSetting=elicitation,
                )
                sid = criado_s["slotId"]
            prioridades.append({"priority": idx, "slotId": sid})

        lex.update_intent(
            botId=bot_id,
            botVersion="DRAFT",
            localeId="pt_BR",
            intentId=intent_id,
            intentName=iname,
            sampleUtterances=utts,
            dialogCodeHook={"enabled": idef["dialog"]},
            fulfillmentCodeHook={"enabled": True},
            slotPriorities=prioridades,
        )

    # Atualiza FallbackIntent para acionar a Lambda
    if "FallbackIntent" in existentes_int:
        lex.update_intent(
            botId=bot_id,
            botVersion="DRAFT",
            localeId="pt_BR",
            intentId=existentes_int["FallbackIntent"],
            intentName="FallbackIntent",
            parentIntentSignature="AMAZON.FallbackIntent",
            dialogCodeHook={"enabled": False},
            fulfillmentCodeHook={"enabled": True},
        )

    # 5. Build, Version e Alias Prod + TestBotAlias
    print("[7/7] Executando Build do idioma pt_BR e vinculando Alias Prod à Lambda...")
    lex.build_bot_locale(botId=bot_id, botVersion="DRAFT", localeId="pt_BR")
    aguardar_status(
        lex.describe_bot_locale,
        "botLocaleStatus",
        {"Built"},
        botId=bot_id,
        botVersion="DRAFT",
        localeId="pt_BR",
    )

    alias_settings = {
        "pt_BR": {
            "enabled": True,
            "codeHookSpecification": {
                "lambdaCodeHook": {
                    "lambdaARN": lambda_arn,
                    "codeHookInterfaceVersion": "1.0",
                }
            },
        }
    }

    # Vincula também no TestBotAlias para testes imediatos no console do Lex
    lex.update_bot_alias(
        botId=bot_id,
        botAliasId="TSTALIASID",
        botAliasName="TestBotAlias",
        botVersion="DRAFT",
        botAliasLocaleSettings=alias_settings,
    )

    ver_resp = lex.create_bot_version(
        botId=bot_id,
        botVersionLocaleSpecification={"pt_BR": {"sourceBotVersion": "DRAFT"}},
    )
    bot_version = ver_resp["botVersion"]
    aguardar_status(
        lex.describe_bot_version,
        "botStatus",
        {"Available"},
        botId=bot_id,
        botVersion=bot_version,
    )

    aliases = lex.list_bot_aliases(botId=bot_id).get("botAliasSummaries", [])
    prod_alias = next((a for a in aliases if a["botAliasName"] == "Prod"), None)
    if prod_alias:
        lex.update_bot_alias(
            botId=bot_id,
            botAliasId=prod_alias["botAliasId"],
            botAliasName="Prod",
            botVersion=bot_version,
            botAliasLocaleSettings=alias_settings,
        )
    else:
        lex.create_bot_alias(
            botId=bot_id,
            botAliasName="Prod",
            botVersion=bot_version,
            botAliasLocaleSettings=alias_settings,
        )

    print(f"\nSUCESSO! Bot '{nome_bot}' (botId={bot_id}, Version={bot_version}, Alias='Prod') criado, compilado e vinculado à Lambda '{nome_lambda}' em {regiao}!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Provisiona o Bot Lex V2 PV-EletroLar-Bot.")
    parser.add_argument("--region", default="us-west-2", help="Região AWS (default: us-west-2).")
    parser.add_argument("--lambda-name", default="PV-PosVendaFulfillment", help="Nome da função Lambda.")
    args = parser.parse_args()
    provisionar_bot_lex(regiao=args.region, nome_lambda=args.lambda_name)


if __name__ == "__main__":
    main()

# Configuração do Bot Amazon Lex V2 (`PV-EletroLar-Bot`)

Este diretório armazena a especificação sanitizada (Zero-Leak) do bot conversacional **Amazon Lex V2** em Português do Brasil (`pt_BR`) utilizando a voz neural **Camila** (Amazon Polly).

## 1. Intenções Mapeadas (100% Aderente ao PDF do Case 3)

| Intenção | Cenário do PDF | Slots Coletados | Code Hooks Habilitados |
| :--- | :--- | :--- | :--- |
| `AcionarGarantiaDefeito` | **Cenário 1 — Defeito no produto** | `ModeloProduto`, `NumeroSerie`, `NumeroNotaFiscal`, `DescricaoDefeito` | `DialogCodeHook` + `FulfillmentCodeHook` |
| `LocalizarAssistenciaTecnica` | **Cenário 2 — Localização de assistência** | `CepOuCidade` (Obrigatório), `CategoriaProduto` (Opcional) | `DialogCodeHook` + `FulfillmentCodeHook` |
| `SolicitarTrocaDevolucao` | **Cenário 3 — Troca / devolução** | `NumeroNotaFiscal`, `ModeloProduto`, `MotivoSolicitacao` | `DialogCodeHook` + `FulfillmentCodeHook` |
| `FalarComAtendente` | **Cenário 4 — Transbordo para agente** | *(Sem slots — usa contexto `pv_*` já coletado)* | `FulfillmentCodeHook` |
| `FallbackIntent` | **Contingência Conversacional** | *(Transfere após 2 tentativas sem resolução)* | `FulfillmentCodeHook` |

## 2. Vinculação com a AWS Lambda (`PV-PosVendaFulfillment`)

No Console do Amazon Lex V2:
1. Abra o bot `PV-EletroLar-Bot` $\rightarrow$ **Aliases** $\rightarrow$ `Prod` $\rightarrow$ idioma **Portuguese (Brazil) (`pt_BR`)**.
2. Em **Lambda function**, selecione `PV-PosVendaFulfillment` (versão `$LATEST` ou alias publicado).
3. No Amazon Connect (**Flows** $\rightarrow$ **Amazon Lex**), adicione o bot `PV-EletroLar-Bot` (Alias `Prod`, região `us-west-2`) para liberar a invocação pelo bloco `ConnectParticipantWithLexBot`.

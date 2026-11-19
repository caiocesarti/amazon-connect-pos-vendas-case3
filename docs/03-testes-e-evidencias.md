# 03 — Roteiro de Testes End-to-End (E2E), Evidências de Tela e Logs de Interações

> **Entregável Obrigatório do PDF (Case 3 — Varejo: Pós-Venda e Suporte de Eletrodomésticos):**  
> *"Teste end-to-end dos 3 cenários com prints de tela e log de interações"*  
> *"Experiência de transbordo com contexto preservado: agente recebe histórico completo da conversa"*

---

## 1. Matriz de Casos de Teste Homologados (`CT-01` a `CT-08`)

| ID | Cenário do PDF / Pilar | Entrada do Cliente (Chat Online ou Voz) | Resultado Esperado & Atributos `pv_*` | Status |
| :--- | :--- | :--- | :--- | :--- |
| **CT-01** | **Cenário 1 — Defeito no produto (Garantia Ativa)** | *"Minha lavadora série EL-LAV-2026-8841 nota NF-100201 parou de funcionar e o painel não liga"* | Bot valida NF no DynamoDB, confirma garantia `ATIVA` até `2027-11-14`, aciona garantia automaticamente com protocolo `PV-YYYYMMDD-XXXX` e vincula a autorizada `TecnoLar Paulista`. | ✅ Homologado na AWS |
| **CT-02** | **Cenário 2 — Localização de assistência por CEP** | *"Buscar assistência autorizada no CEP 01310-200"* | Bot consulta faixa de CEP no DynamoDB e retorna `TecnoLar Paulista` com endereço (`Av. Paulista, 1842`), telefone (`(11) 3003-4010`) e horário. | ✅ Homologado na AWS |
| **CT-03** | **Cenário 2B — Localização de assistência por Cidade** | *"Qual a assistência técnica autorizada em Salvador?"* | Bot normaliza cidade, consulta DynamoDB e retorna `BahiaTec EletroLar — Caminho das Árvores`, telefone `(71) 3341-8800` e horário. | ✅ Homologado na AWS |
| **CT-04** | **Cenário 3 — Troca / Devolução com protocolo no chat** | *"Quero trocar o micro-ondas 32L da nota fiscal NF-100203"* $\rightarrow$ *"arrependimento em até 7 dias"* | Bot valida prazo CDC (Art. 49), registra o caso no DynamoDB com status `ELEGIVEL` e envia o protocolo `PV-YYYYMMDD-XXXX` no chat online. | ✅ Homologado na AWS |
| **CT-05** | **Cenário 4 — Transbordo Humano com Contexto Preservado** | *"Quero falar com um atendente"* | Bot gera protocolo `PV-YYYYMMDD-XXXX`, transfere para `PV-Fila-Suporte-PosVenda-N1` (`pv_transbordo=TRUE`, `pv_motivo_transbordo=SOLICITACAO_CLIENTE`) preservando histórico no Agent Workspace. | ✅ Homologado na AWS |
| **CT-06** | **Cenário 4B — Transbordo (Garantia Expirada / Fora de Cobertura)** | *"Acionar garantia da Geladeira FrostFree série EL-GEL-2024-1102 nota NF-100202 que parou de gelar"* | Bot identifica garantia `EXPIRADA`, gera protocolo e encaminha para fila humana (`pv_motivo_transbordo=GARANTIA_EXPIRADA`) com contexto pré-preenchido. | ✅ Validado no Pytest |
| **CT-07** | **Guardrail Crítico — Risco Elétrico / Doméstico** | *"Socorro, está saindo fumaça e cheiro de queimado da minha lavadora!"* | Bot orienta desligar da tomada imediatamente, seta `pv_risco_seguranca=TRUE` e transfere com prioridade máxima (`ALERTA_SEGURANCA_ELETRICA`). | ✅ Validado no Pytest |
| **CT-08** | **Guardrail Preventivo — Tentativa de Reparo Caseiro** | *"Como abrir o gabinete do micro-ondas para trocar o capacitor em casa?"* | Bot bloqueia orientação de desmontagem caseira, alerta sobre risco de alta tensão e orienta atendimento oficial. | ✅ Validado no Pytest |

---

## 2. Evidências dos Testes End-to-End no Ambiente AWS Real

### 2.1. Cenário 1 — Defeito no Produto e Acionamento Automático de Garantia (`CT-01`)
- **Entrada:** `Minha lavadora série EL-LAV-2026-8841 nota NF-100201 parou de funcionar e o painel não liga` $\rightarrow$ `parou de funcionar`
- **Validação:** Garantia confirmada como `ATIVA` até `2027-11-14` (consulta ao DynamoDB `PV-AssistenciasGarantia`), geração de protocolo determinístico `PV-20261119-1937` e vinculação imediata do posto `TecnoLar Paulista` com endereço, telefone e prazo de visita em até 24h úteis.

| 1A. Coleta dos Dados e Pergunta do Defeito | 1B. Garantia Ativa e Protocolo Gerado | 1C. Assistência Autorizada Vinculada |
| :---: | :---: | :---: |
| ![Cenário 1A](evidencias/01a-cenario1-defeito-pergunta-bot.png) | ![Cenário 1B](evidencias/01b-cenario1-garantia-acionada-protocolo.png) | ![Cenário 1C](evidencias/01c-cenario1-autorizada-vinculada.png) |

#### Log de Interação — Cenário 1 (Transcrição Real):
```text
Cliente EletroLar: Minha lavadora série EL-LAV-2026-8841 nota NF-100201 parou de funcionar e o painel não liga
Assistente Camila: Pode descrever brevemente o que está acontecendo com o produto (ex.: parou de funcionar, não centrifuga, não gela)?
Cliente EletroLar: parou de funcionar
Assistente Camila: Garantia acionada automaticamente com sucesso!

• Protocolo de Garantia: PV-20261119-1937
• Produto: Lavadora EletroLar 12kg Turbo Inverter (Série: EL-LAV-2026-8841)
• Nota Fiscal: NF-100201 — Garantia ATIVA até 2027-11-14
• Assistência Autorizada Vinculada: TecnoLar Paulista — Assistência Autorizada Central
• Endereço: Av. Paulista, 1842, Conj. 14, Bela Vista — São Paulo/SP (CEP 01310-200)
• Telefone: (11) 3003-4010
• Horário: Seg a Sex das 08h às 18h | Sáb das 08h às 13h
• Prazo de Visita / Atendimento: Até 24 horas úteis

Central EletroLar: A EletroLar agradece o seu contato! Caso precise de suporte adicional, tenha em mãos o seu protocolo PV-20261119-1937. Tenha um ótimo dia!
```

---

### 2.2. Cenário 2 — Localização de Assistência Técnica Autorizada por Cidade e CEP (`CT-02` / `CT-03`)
- **Entrada:** `Qual a assistência técnica autorizada em Salvador?`
- **Validação:** O bot normaliza o município consultando a tabela `PV-AssistenciasGarantia` no DynamoDB e retorna a unidade **BahiaTec EletroLar** (Unidade Caminho das Árvores), com endereço completo na Av. Tancredo Neves, telefone `(71) 3341-8800` e horário de funcionamento.

| Localização de Posto Autorizado em Salvador/BA no Widget Oficial |
| :---: |
| ![Cenário 2 - Busca de Assistência Autorizada](evidencias/02-cenario2-assistencia-cep-cidade.png) |

#### Log de Interação — Cenário 2 (Transcrição Real):
```text
Cliente EletroLar: Qual a assistência técnica autorizada em Salvador?
Assistente Camila: Localizei a assistência técnica autorizada mais próxima para Salvador:

• Autorizada: BahiaTec EletroLar — Unidade Caminho das Árvores (AST-BA-01)
• Endereço: Av. Tancredo Neves, 1632, Térreo, Caminho das Árvores — Salvador/BA (CEP 41820-020)
• Telefone: (71) 3341-8800
• Horário de Atendimento: Seg a Sex das 08h às 18h | Sáb das 08h às 13h
• Especialidades: Linha Branca Completa e Climatização
```

---

### 2.3. Cenário 3 — Solicitação de Troca / Devolução com Protocolo no Chat (`CT-04`)
- **Entrada:** `Quero trocar o micro-ondas 32L da nota fiscal NF-100203` $\rightarrow$ `arrependimento em até 7 dias`
- **Validação:** O sistema calcula a data de compra da NF-100203, confirma que está dentro da janela de 7 dias do Código de Defesa do Consumidor (CDC Art. 49), registra o caso no DynamoDB e entrega o protocolo oficial **`PV-20261119-9843`** diretamente no chat online com agendamento de coleta reversa domiciliar em até 48h úteis.

| 3A. Identificação da Solicitação e Motivo | 3B. Protocolo e Confirmação de Coleta | 3C. Atributos Gravados no Contact Details |
| :---: | :---: | :---: |
| ![Cenário 3A](evidencias/03-cenario3-troca-devolucao-protocolo.png) | ![Cenário 3B](evidencias/03b-cenario3-troca-protocolo.png) | ![Cenário 3C](evidencias/03c-cenario3-contact-details-atributos.png) |

#### Log de Interação — Cenário 3 (Transcrição Real):
```text
Cliente EletroLar: Quero trocar o micro-ondas 32L da nota fiscal NF-100203
Assistente Camila: Qual é o motivo da troca ou devolução (ex.: arrependimento em até 7 dias, produto avariado na entrega ou defeito)?
Cliente EletroLar: arrependimento em até 7 dias
Assistente Camila: Solicitação de Troca / Devolução registrada com sucesso!

• Protocolo Oficial: PV-20261119-9843
• Nota Fiscal: NF-100203
• Produto: Micro-ondas EletroLar Chef 32L Espelhado
• Motivo Registrado: Arrependimento 7 dias
• Status: ELEGÍVEL (Dentro do prazo legal — Coleta reversa domiciliar autorizada)
• Próximo Passo: Guarde este protocolo (PV-20261119-9843). Nossa equipe logística realizará a coleta em até 48h úteis.

Central EletroLar: A EletroLar agradece o seu contato! Caso precise de suporte adicional, tenha em mãos o seu protocolo PV-20261119-9843. Tenha um ótimo dia!
```

---

### 2.4. Cenário 4 — Transbordo Humano com Preservação Integral de Contexto (`CT-05`)
- **Entrada do Cliente:** `Quero falar com um atendente`
- **Comportamento do Contact Flow (`PV-Transbordo-N1`):**
  1. O bot gera o protocolo de atendimento **`PV-20261119-5103`** e avisa o cliente.
  2. A chamada é roteada para a fila **`PV-Fila-Suporte-PosVenda-N1`**.
  3. O atendente humano no **Agent Workspace v2 (CCP)** recebe o pop-up com a notificação sonora e o histórico completo do que foi conversado.
  4. O Amazon Connect armazena nos atributos da sessão os metadados:
     - `pv_transbordo = TRUE`
     - `pv_motivo_transbordo = SOLICITACAO_CLIENTE`
     - `pv_protocolo = PV-20261119-5103`
     - `pv_jornada = ATENDIMENTO_HUMANO`
     - `pv_fila_destino = PV-Fila-Suporte-PosVenda-N1`

| 4A. Notificação e Protocolo no Chat | 4B. Conexão do Atendente Humano | 4C. Atendimento no Agent Workspace | 4D. Auditoria de Atributos no Contact Details |
| :---: | :---: | :---: | :---: |
| ![Cenário 4A](evidencias/04a-cenario4-transbordo-chat-cliente.png) | ![Cenário 4B](evidencias/04b-cenario4-transbordo-chat-conectado.png) | ![Cenário 4C](evidencias/04c-cenario4-agent-workspace-ccp.png) | ![Cenário 4D](evidencias/04d-cenario4-contact-details-atributos-transbordo.png) |

---

## 3. Pilares Complementares de Arquitetura

### 3.1. Amazon Q in Connect (Assistência de IA Generativa ao Operador)
Integração do domínio de conhecimento `PV-Q-Assistant` com bucket S3 contendo os runbooks operacionais (`knowledge-base/`):

| Domínio do Amazon Q in Connect Integrado |
| :---: |
| ![Amazon Q Domain e S3 Knowledge Base](evidencias/05-amazon-q-knowledge-base.png) |

---

### 3.2. Logs de Interações e Métricas de Execução (CloudWatch Log Analytics)
Execução da query de auditoria no log group `/aws/lambda/PV-PosVendaFulfillment` comprovando os tempos reais de execução Serverless da Lambda em Python 3.12 (médias de 1,7 ms a 4,1 ms, com consumo de apenas 41 MB a 91 MB de memória RAM):

| CloudWatch Log Analytics — Métricas e Eventos Reais da Lambda |
| :---: |
| ![CloudWatch Logs Insights Execuções Reais](evidencias/06-cloudwatch-logs-lambda.png) |

---

## 4. Conclusão dos Entregáveis

| Entregável Exigido no PDF | Status | Evidência Comprobatória |
| :--- | :---: | :--- |
| **Cenário 1:** Defeito no produto, coleta de modelo/série/NF e acionamento automático | **100% Concluído** | Imagens `01a`, `01b` e `01c` + Protocolo `PV-20261119-1937` |
| **Cenário 2:** Localização de autorizada por CEP e Cidade com endereço/fone/horário | **100% Concluído** | Imagem `02` + Unidade BahiaTec Caminho das Árvores |
| **Cenário 3:** Solicitação de troca com validação CDC e protocolo enviado no chat | **100% Concluído** | Imagens `03`, `03b` e `03c` + Protocolo `PV-20261119-9843` |
| **Cenário 4:** Transbordo humano preservando histórico e atributos de contexto | **100% Concluído** | Imagens `04a`, `04b`, `04c` e `04d` + Protocolo `PV-20261119-5103` |
| **Logs de Interações:** Rastreabilidade e auditoria de execução | **100% Concluído** | Imagens `03c`, `04d` e `06` + Transcrições completas |

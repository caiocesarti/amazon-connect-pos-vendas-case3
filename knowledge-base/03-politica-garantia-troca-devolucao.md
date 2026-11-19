# KB-003: Política Oficial de Garantia, Troca, Devolução e Transbordo N1 — EletroLar Varejo

**Categoria:** Políticas Comerciais e CDC / Procedimentos de Pós-Venda (Amazon Q in Connect)  
**Público-alvo:** Bot Amazon Lex V2, Assistente Amazon Q in Connect e Agentes N1 (Agent Workspace / CCP v2)  
**Última Atualização:** Novembro/2026

---

## 1. Acionamento Automático de Garantia (12 Meses)

- **Cobertura Total:** Todos os eletrodomésticos comercializados pela **EletroLar Varejo** possuem **12 meses de garantia total** (90 dias de garantia legal conforme Art. 26 do CDC + 9 meses de garantia contratual complementar), contados a partir da data de emissão da Nota Fiscal (`NF-100xxx`).
- **Requisitos para Abertura Automática pelo Bot (`AcionarGarantiaDefeito`):**
  1. Modelo do produto (`ModeloProduto`);
  2. Número de série (`NumeroSerie` no padrão `EL-<CAT>-<ANO>-<FINAL>`);
  3. Número da Nota Fiscal (`NumeroNotaFiscal` no padrão `NF-100xxx`);
  4. Breve relato do defeito (`DescricaoDefeito`).
- **Resultado Esperado:**
  - **Garantia `ATIVA`:** O sistema gera automaticamente a Ordem de Serviço / Protocolo no formato `PV-YYYYMMDD-XXXX`, vincula a assistência técnica autorizada mais próxima do CEP do cliente e informa o prazo de atendimento domiciliar (produtos de grande porte: lavadoras, geladeiras, fogões e ar-condicionado) ou balcão (micro-ondas e portáteis).
  - **Garantia `EXPIRADA` (ex.: `NF-100202` ou `NF-100208`):** O bot informa de maneira transparente a data de vencimento da garantia e **transfere automaticamente para um Agente Humano N1** (`pv_motivo_transbordo = GARANTIA_EXPIRADA`) para oferta de orçamento oficial sem compromisso ou desconto em renovação.

---

## 2. Política de Troca e Devolução (`SolicitarTrocaDevolucao`)

### 2.1. Direito de Arrependimento ou Troca Direta (Até 7 Dias Corridos — Art. 49 do CDC)
- Clientes que receberam o produto há **até 7 dias corridos** (ex.: `NF-100201`, `NF-100203`, `NF-100205`, `NF-100206`, `NF-100209`, `NF-100210`) têm direito à abertura imediata do processo de **troca por novo exemplar** ou **devolução com estorno integral**.
- O bot coleta `NumeroNotaFiscal`, `ModeloProduto` e `MotivoSolicitacao` (ex.: *arrependimento*, *produto avariado na entrega*, *voltagem incorreta* ou *defeito nos primeiros dias*), registra o caso no DynamoDB e **envia o protocolo `PV-YYYYMMDD-XXXX` imediatamente no chat online**.

### 2.2. Solicitações Após 7 Dias Corridos (Ex.: `NF-100204`, `NF-100207`)
- Quando a compra ultrapassou os 7 dias corridos de arrependimento mas permanece com **garantia de fábrica ativa**, a solicitação é coberta pelo fluxo de **reparo gratuito em assistência técnica autorizada** (Art. 18 do CDC — prazo máximo legal de 30 dias para saneamento do vício).
- Caso o cliente insista na troca ou relate reincidência de Ordem de Serviço sem solução, o bot registra os dados e realiza o **transbordo assistido para a fila `PV-Fila-Suporte-PosVenda-N1`** (`pv_motivo_transbordo = FORA_PRAZO_TROCA`).

---

## 3. Regiões Sem Assistência Técnica Presencial (`CEP_SEM_ASSISTENCIA`)

- Caso o CEP ou município informado (ex.: `69900-000` — Rio Branco/AC, `78900-050` — Porto Velho/RO, `57020-000` — Maceió/AL) não possua posto autorizado presencial num raio de 30 km:
  1. O bot informa claramente que não há unidade física credenciada naquele município;
  2. Gera protocolo preventivo e **transfere o atendimento para o especialista N1** (`pv_motivo_transbordo = CEP_SEM_ASSISTENCIA`) para emissão de código de postagem reversa gratuita (portáteis) ou agendamento de técnico itinerante credenciado (linha branca pesada).

---

## 4. Padrão de Transbordo para o Agent Workspace (CCP v2)

Ao receber um atendimento transferido na fila `PV-Fila-Suporte-PosVenda-N1`, o agente N1 **nunca deve pedir ao cliente que repita dados já coletados**. O agente deve ler os atributos de sessão `pv_*` exibidos no painel de contato:
- `pv_resumo`: Síntese executiva em uma linha;
- `pv_jornada`, `pv_nota_fiscal`, `pv_modelo`, `pv_numero_serie`, `pv_status_garantia`, `pv_cep_cidade`, `pv_protocolo` e `pv_motivo_transbordo`;
- Histórico completo das mensagens trocadas com o bot no componente nativo de Chat do Amazon Connect.

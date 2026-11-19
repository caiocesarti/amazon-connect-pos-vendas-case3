# KB-001: Guia Rápido de Troubleshooting — Lavadoras e Lava & Seca EletroLar

**Categoria:** Suporte Técnico N1 / Autoatendimento Assistido (Amazon Q in Connect)  
**Linhas Atendidas:** `Lavadora EletroLar 10kg Essential`, `Lavadora EletroLar 12kg Turbo Inverter`, `Lavadora EletroLar 15kg Ultra Wash Vapor`, `Lava e Seca EletroLar 11kg Smart Wi-Fi`  
**Última Atualização:** Novembro/2026

---

## 1. Alerta Obrigatório de Segurança e Preservação de Garantia

> **ATENÇÃO (GUARDRAIL DE SEGURANÇA):**  
> Jamais oriente o cliente a desmontar o painel eletrônico, abrir a tampa traseira, jumpear travas de porta ou manusear fiação interna. Qualquer intervenção não autorizada **invalida a garantia contratual de 12 meses** e expõe o consumidor a risco de choque elétrico. Se o cliente relatar **fumaça, cheiro de queimado, faíscas ou choque no gabinete**, oriente a desligar imediatamente da tomada/disjuntor e realize o **transbordo prioritário para o Especialista N1** (`pv_motivo_transbordo = ALERTA_SEGURANCA_ELETRICA`).

---

## 2. Cenários de Verificação Básica (Sem Perda de Garantia)

### 2.1. Máquina de lavar parou de funcionar / Não liga
1. **Alimentação elétrica:** Solicite ao cliente verificar se o cabo de força está firmemente conectado a uma tomada exclusiva (127V ou 220V conforme etiqueta do número de série `EL-LAV-*`) e sem uso de adaptadores ("benjamins" ou extensões).
2. **Disjuntor e queda de energia:** Oriente a testar a tomada com outro aparelho pequeno ou checar o quadro de disjuntores.
3. **Trava de segurança da tampa/porta:** Nos modelos *Inverter* e *Lava e Seca*, o ciclo só inicia após o clique audível da trava eletromagnética da porta.
4. **Persistindo o sintoma:** Coletar **Modelo**, **Número de Série** e **Nota Fiscal** para acionar automaticamente a garantia e gerar o protocolo `PV-YYYYMMDD-XXXX`.

### 2.2. Lavadora não centrifuga ou não solta a água
1. **Desbalanceamento de carga (Código `UE`):** Roupas pesadas concentradas de um único lado do cesto impedem a rotação por segurança. Oriente a pausar o ciclo, redistribuir as peças uniformemente e fechar a tampa.
2. **Altura da mangueira de drenagem (Código `E2`):** A mangueira de saída deve estar posicionada entre **85 cm e 120 cm** do piso, sem dobras ou estrangulamentos.
3. **Filtro de fiapos / bomba de drenagem (Acesso frontal externo):** Nos modelos *Lava e Seca 11kg*, o cliente pode limpar apenas o filtro coletor de moedas/fiapos localizado na portinhola frontal inferior (com o aparelho desligado da tomada).

### 2.3. Lavadora não enche de água (Código `E1`)
1. Confirmar se o registro de água da lavanderia está totalmente aberto.
2. Verificar se a telinha externa da mangueira de entrada (junto à torneira) apresenta obstrução por resíduos da rede hidráulica.

---

## 3. Tabela de Códigos de Painel EletroLar

| Código no Visor | Significado Técnico | Ação Recomendada ao Agente / Bot |
| :--- | :--- | :--- |
| `E1` | Tempo limite de entrada de água excedido | Checar torneira aberta e pressão da rede hidráulica. |
| `E2` | Falha de drenagem / escoamento lento | Checar dobras na mangueira de saída; se persistir, acionar garantia. |
| `E3` / `dE` | Porta ou tampa destravada | Reabrir e fechar a porta até ouvir o travamento; se persistir, acionar garantia. |
| `UE` | Cesto desbalanceado na centrifugação | Redistribuir roupas no tambor. |
| `HE` / `tE` | Falha no sensor térmico ou resistência | **Proibido reparo caseiro.** Acionar garantia imediatamente (`AcionarGarantiaDefeito`). |
| `LE` / `CE` | Sobrecarga no motor Inverter | Desligar da tomada por 5 min; se retornar, abrir Ordem de Serviço em garantia. |

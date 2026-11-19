# Política de Segurança DevSecOps & Zero-Leak (SECURITY.md)

Este repositório adota uma política estrita **Zero-Leak** para garantir que nenhum dado sensível, identificador de conta real da AWS ou credencial de integração seja exposto no histórico público do Git.

## 1. Placeholders Obrigatórios

Em qualquer arquivo versionado (`.env.example`, Contact Flows em `connect-flows/`, exportações do Lex em `lex/`, scripts e documentação), utilize **exclusivamente** os placeholders padronizados:

| Tipo de Dado | Placeholder Oficial |
| :--- | :--- |
| AWS Account ID (12 dígitos) | `000000000000` ou `<ACCOUNT_ID>` |
| Região AWS | `us-west-2` ou `<REGION>` |
| Alias da Instância Amazon Connect | `<INSTANCE_ALIAS>` |
| ID do Widget / Script | `<WIDGET_ID>` / `<WIDGET_SCRIPT_ID>` |
| Snippet ID do Widget | `<WIDGET_SNIPPET_ID>` |

## 2. Isolamento do Snippet do Amazon Connect

- O snippet real do Communications Widget **jamais** deve ser inserido em `landing/index.html` ou `landing/widget-snippet.example.html`.
- Para testes locais, salve o snippet em `landing/widget-snippet.local.html` (bloqueado no `.gitignore`).
- Para deploy na Vercel, configure a variável de ambiente `CONNECT_WIDGET_SNIPPET` (ou `CONNECT_WIDGET_SNIPPET3`) no painel do projeto; os scripts `scripts/injetar_widget.js` / `scripts/injetar_widget.py` geram `landing/connect-widget-loader.js` em tempo de build com proteção FinOps contra crawlers (`navigator.webdriver`) e limite de mensagens no `localStorage`.

## 3. Auditoria Automatizada

Antes de qualquer commit ou push, execute:

```bash
python scripts/verificar_segredos.py
```

O script retorna código `0` apenas quando 100% dos arquivos auditados estão livres de Account IDs reais, ARNs reais, chaves `AKIA`/`ASIA`, tokens Vercel/GitHub e snippets reais do widget.

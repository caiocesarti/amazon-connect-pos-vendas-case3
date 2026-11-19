#!/usr/bin/env python3
"""Injetor Multiplataforma do Snippet do Communications Widget — Amazon Connect (EletroLar Varejo).

Suporta duas fontes seguras (Zero-Leak) para não expor IDs no repositório Git:
1. Variável de ambiente `CONNECT_WIDGET_SNIPPET` (ideal para build na Vercel / CI)
2. Arquivo local `landing/widget-snippet.local.html` (ignorado pelo `.gitignore`)

Inclui Camada de Proteção FinOps:
- Bloqueio automático de WebDrivers / Crawlers (`navigator.webdriver`)
- Limite de interações por navegador (`localStorage`) para proteger a cota do AWS Free Tier.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SNIPPET_LOCAL = RAIZ / "landing" / "widget-snippet.local.html"
INDEX_FILE = RAIZ / "landing" / "index.html"
LOADER_FILE = RAIZ / "landing" / "connect-widget-loader.js"
PLACEHOLDER = "<!-- AMAZON_CONNECT_WIDGET_PLACEHOLDER -->"
SCRIPT_TAG_EXTERNA = '<script src="./connect-widget-loader.js" defer></script>'
MAX_MENSAGENS_PADRAO = int(os.environ.get("MAX_WIDGET_MESSAGES_PER_VISITOR", "30"))


def obter_snippet(env_snippet: str | None = None) -> str | None:
    if env_snippet is not None and env_snippet.strip():
        return env_snippet.strip()
    for var_name in ("CONNECT_WIDGET_SNIPPET3", "CONNECT_WIDGET_SNIPPET"):
        valor_env = os.environ.get(var_name, "").strip()
        if valor_env:
            return valor_env
    if SNIPPET_LOCAL.is_file():
        texto = SNIPPET_LOCAL.read_text(encoding="utf-8").strip()
        if texto:
            return texto
    return None


def gerar_codigo_loader_finops(snippet_original: str, limite_mensagens: int = 30) -> str:
    """Gera o arquivo JS externo com camada FinOps (anti-bot e limite de cota Free Tier)."""
    corpo_js = re.sub(r"<\/?script[^>]*>", "", snippet_original, flags=re.IGNORECASE).strip()
    corpo_js = re.sub(r"(?<![\w$.])s\s*=\s*d\.createElement", "var s=d.createElement", corpo_js)

    if "customerDisplayName" not in corpo_js:
        corpo_js += """
  amazon_connect('customerDisplayName', function(callback) {
    callback('Cliente EletroLar');
  });"""

    if "customChatInitiateAttributes" not in corpo_js:
        corpo_js += """
  amazon_connect('customChatInitiateAttributes', {
    pv_origem: 'landing',
    pv_canal: 'CHAT'
  });"""

    return f"""/* ==========================================================================
   PROTEÇÃO FINOPS & ANTI-BOT (LIMITE DE {limite_mensagens} MENSAGENS POR VISITANTE)
   EletroLar Varejo — Central de Pós-Venda e Suporte de Eletrodomésticos
   ========================================================================== */
(function() {{
  'use strict';
  var MAX_MSG = {limite_mensagens};
  var STORAGE_KEY = 'pv_aws_connect_msg_count_v1';

  // 1. Bloqueia crawlers e navegadores headless automatizados
  if (navigator.webdriver) {{
    console.warn('[FinOps Guard] Automação detectada (navigator.webdriver). Widget AWS desativado; utilize o Simulador Local.');
    return;
  }}

  // 2. Verifica cota de mensagens por visitante no navegador
  var usadas = parseInt(localStorage.getItem(STORAGE_KEY) || '0', 10);
  if (usadas >= MAX_MSG) {{
    console.warn('[FinOps Guard] Limite de ' + MAX_MSG + ' mensagens atingido neste navegador para proteção do Free Tier.');
    return;
  }}

  // 3. Contabiliza envios de mensagens (Enter no widget) até o limite de {limite_mensagens}
  window.addEventListener('keydown', function(e) {{
    if (e.key === 'Enter' && !e.shiftKey) {{
      var atual = parseInt(localStorage.getItem(STORAGE_KEY) || '0', 10) + 1;
      localStorage.setItem(STORAGE_KEY, String(atual));
    }}
  }}, true);

  // 4. Inicializa o Communications Widget Oficial do Amazon Connect
  {corpo_js}
}})();
"""


def reverter_injecao() -> int:
    if LOADER_FILE.is_file():
        LOADER_FILE.unlink()
    if INDEX_FILE.is_file():
        conteudo = INDEX_FILE.read_text(encoding="utf-8")
        if SCRIPT_TAG_EXTERNA in conteudo:
            INDEX_FILE.write_text(conteudo.replace(SCRIPT_TAG_EXTERNA, PLACEHOLDER), encoding="utf-8")
    print("[WIDGET] Placeholder restaurado em landing/index.html e connect-widget-loader.js removido.")
    return 0


def injetar(limite: int = MAX_MENSAGENS_PADRAO) -> int:
    snippet = obter_snippet()
    if not snippet:
        print("[INFO] Nenhum snippet encontrado em CONNECT_WIDGET_SNIPPET ou landing/widget-snippet.local.html.")
        print("Mantendo landing/index.html no modo de pré-visualização interativa limpa.")
        return 0

    conteudo_index = INDEX_FILE.read_text(encoding="utf-8")
    codigo_js = gerar_codigo_loader_finops(snippet, limite_mensagens=limite)
    LOADER_FILE.write_text(codigo_js, encoding="utf-8")

    if PLACEHOLDER in conteudo_index:
        novo_conteudo = conteudo_index.replace(PLACEHOLDER, SCRIPT_TAG_EXTERNA)
        INDEX_FILE.write_text(novo_conteudo, encoding="utf-8")

    print(
        f"[WIDGET] OK - Snippet do Amazon Connect compilado em landing/connect-widget-loader.js "
        f"(Proteção FinOps: máx. {limite} msgs/visitante)."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(ValueError, OSError):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Injeta ou reverte o widget do Amazon Connect.")
    parser.add_argument("--reverter", action="store_true", help="Restaura o placeholder limpo para commit.")
    parser.add_argument("--limite", type=int, default=MAX_MENSAGENS_PADRAO, help="Limite de mensagens FinOps.")
    args = parser.parse_args(argv)

    if args.reverter:
        return reverter_injecao()
    return injetar(limite=args.limite)


if __name__ == "__main__":
    sys.exit(main())

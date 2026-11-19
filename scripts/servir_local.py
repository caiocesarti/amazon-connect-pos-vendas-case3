#!/usr/bin/env python3
"""Servidor local de desenvolvimento e laboratório (Portal Web + Simulador Lambda Lex V2).

Uso:
    python scripts/servir_local.py --porta 8080
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
PASTA_LANDING = RAIZ / "landing"
sys.path.insert(0, str(RAIZ / "lambda" / "pos_venda_fulfillment"))

from handler import lambda_handler  # noqa: E402


class LabRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/lex":
            tamanho = int(self.headers.get("Content-Length", "0"))
            corpo_raw = self.rfile.read(tamanho).decode("utf-8") if tamanho > 0 else "{}"
            try:
                payload: dict[str, Any] = json.loads(corpo_raw)
                resposta = lambda_handler(payload, None)
                dados_bytes = json.dumps(resposta, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(dados_bytes)))
                self.end_headers()
                self.wfile.write(dados_bytes)
            except Exception as exc:
                erro_bytes = json.dumps({"erro": str(exc)}, ensure_ascii=False).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(erro_bytes)))
                self.end_headers()
                self.wfile.write(erro_bytes)
            return

        self.send_error(404, "Endpoint nao encontrado")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Servidor local do Portal Pós-Venda EletroLar.")
    parser.add_argument("--porta", type=int, default=8080, help="Porta HTTP (default: 8080).")
    args = parser.parse_args(argv)

    handler_cls = partial(LabRequestHandler, directory=str(PASTA_LANDING))
    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), handler_cls)
    print(f"[LAB LOCAL] Portal EletroLar disponível em http://localhost:{args.porta}")
    print("[LAB LOCAL] Pressione Ctrl+C para encerrar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[LAB LOCAL] Servidor encerrado.")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

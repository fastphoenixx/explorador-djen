#!/usr/bin/env python3
"""Explorador DJEN + consulta pública TJDFT — protótipo local de teste.

Uso:  python3 servidor.py   →  http://localhost:8791
Só stdlib. O servidor existe porque as APIs não liberam CORS pro navegador.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORTA = 8791
DJEN = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
TJDFT = "https://pje-consultapublica-api.tjdft.jus.br/v1"
UA = {"User-Agent": "Mozilla/5.0 (explorador-djen)"}
PARAMS_DJEN = {
    "numeroOab", "ufOab", "nomeAdvogado", "nomeParte", "numeroProcesso", "texto",
    "dataDisponibilizacaoInicio", "dataDisponibilizacaoFim", "siglaTribunal",
    "numeroComunicacao", "pagina", "itensPorPagina", "meio",
}
PAGINA = Path(__file__).with_name("index.html")


def buscar(url, headers=None, timeout=60):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


def json_de(url):
    with buscar(url) as r:
        return json.load(r)


def paginado(url):
    itens, pagina = [], 0
    while pagina < 20:  # trava de segurança
        d = json_de(f"{url}?page={pagina}")
        itens += d.get("result") or []
        info = d.get("pageInfo") or {}
        if not d.get("result") or info.get("current", 1) >= info.get("last", 1):
            break
        pagina += 1
    return itens


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("·", self.address_string(), fmt % args)

    def responder(self, status, corpo, tipo="application/json; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def json(self, obj, status=200, extra=None):
        self.responder(status, json.dumps(obj, ensure_ascii=False).encode(), extra=extra)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items() if v and v[0].strip()}
        try:
            if url.path in ("/", "/index.html"):
                self.responder(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/djen":
                self.djen(q)
            elif url.path == "/api/tjdft/processo":
                self.tjdft_processo(q)
            elif url.path == "/api/tjdft/validar":
                self.json(json_de(f"{TJDFT}/documentos/{urllib.parse.quote(q['x'])}/validar"))
            elif url.path == "/api/tjdft/pdf":
                self.tjdft_pdf(q)
            else:
                self.json({"erro": "rota não existe"}, 404)
        except urllib.error.HTTPError as e:
            self.json({"erro": f"HTTP {e.code} da API externa", "detalhe": e.read()[:500].decode(errors="ignore")}, 502)
        except KeyError as e:
            self.json({"erro": f"parâmetro obrigatório ausente: {e}"}, 400)
        except Exception as e:  # protótipo: mostra o erro na tela em vez de engolir
            self.json({"erro": f"{type(e).__name__}: {e}"}, 500)

    def djen(self, q):
        params = {k: v for k, v in q.items() if k in PARAMS_DJEN}
        with buscar(f"{DJEN}?{urllib.parse.urlencode(params)}") as r:
            corpo = json.load(r)
            limite = {"x-ratelimit-limit": r.headers.get("x-ratelimit-limit"),
                      "x-ratelimit-remaining": r.headers.get("x-ratelimit-remaining")}
        corpo["_ratelimit"] = limite
        corpo["_url"] = f"{DJEN}?{urllib.parse.urlencode(params)}"
        self.json(corpo)

    def tjdft_processo(self, q):
        busca = json_de(f"{TJDFT}/processos?numeroProcesso={urllib.parse.quote(q['numero'])}")
        achados = busca.get("result") or []
        if not achados:
            return self.json({"erro": "processo não encontrado na consulta pública do TJDFT (sigiloso, de outro tribunal ou número errado)"}, 404)
        proc = achados[0]
        pid = urllib.parse.quote(proc["idProcesso"])
        self.json({
            "processo": proc,
            "dados": json_de(f"{TJDFT}/processos/{pid}/dados").get("result"),
            "movimentacoes": paginado(f"{TJDFT}/processos/{pid}/movimentacoes"),
            "documentos": paginado(f"{TJDFT}/processos/{pid}/documentos"),
        })

    def tjdft_pdf(self, q):
        if "processo" in q:
            alvo = f"{TJDFT}/processos/{urllib.parse.quote(q['processo'])}/imprimir"
        else:
            alvo = f"{TJDFT}/documentos/{urllib.parse.quote(q['id'])}/download"
        with buscar(alvo, {"Accept": "application/pdf", "Content-Type": "application/json"}) as r:
            dados = r.read()
        nome = q.get("nome", "documento") + ".pdf"
        self.responder(200, dados, "application/pdf",
                       {"Content-Disposition": f'inline; filename="{urllib.parse.quote(nome)}"'})


if __name__ == "__main__":
    print(f"Explorador DJEN → http://localhost:{PORTA}")
    ThreadingHTTPServer(("127.0.0.1", PORTA), Handler).serve_forever()

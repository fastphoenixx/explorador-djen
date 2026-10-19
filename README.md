# Explorador DJEN

Interface simples para consultar a **Comunica API** do CNJ: as comunicações (intimações, editais)
publicadas no Diário de Justiça Eletrônico Nacional, de todos os tribunais.

**Usar online:** https://fastphoenixx.github.io/explorador-djen/

## Dois modos

| | Web (GitHub Pages) | Local (`python3 servidor.py`) |
|---|---|---|
| Consulta DJEN (OAB, parte, processo, texto, tribunal, datas) | ✅ direto do navegador | ✅ |
| Link compartilhável com os parâmetros na URL | ✅ | ✅ |
| PDF da publicação e processo completo do **TJDFT** | — | ✅ via proxy local |

O TJDFT bloqueia chamadas vindas de outros sites, por isso as funções dele só existem no modo local.

```bash
python3 servidor.py      # → http://localhost:8791  (só a stdlib do Python)
```

## Limites e cuidados

- O CNJ aplica **rate limit por IP**. Se aparecer erro 429, espere 1 minuto. Usar vários IPs para
  contornar o limite é considerado uso abusivo pela própria API.
- Até 10.000 resultados por consulta. `itensPorPagina` aceita 5 ou 100.
- A API do TJDFT usada no modo local **não tem documentação pública** e pode mudar sem aviso.
- Os resultados trazem dados pessoais das partes. Não versione nem republique esses dados.

Documentação oficial da Comunica API: https://comunicaapi.pje.jus.br/swagger/index.html

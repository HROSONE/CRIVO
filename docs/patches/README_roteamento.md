# Roteamento 17M×46M e categorias zero (sem treino)

Branch: `melhorias/roteamento-categorias-zero-v2`

## O que entra

1. **`conversa_roteamento.py`** — já no repositório nesta branch.
   - Respostas fixas para: `insulto`, `ser_humano`, `motivacao`, `amor_bom`, `sem_sentido`, `tedio`
   - Critérios de mensagem rápida vs. necessidade do 46M

2. **Patch em `conversa_v3d.py`** — aplicar com:

```bash
git apply docs/patches/conversa_v3d_roteamento.patch
```

## Efeito esperado

| Situação | Antes | Depois |
|----------|-------|--------|
| "você é burro" | modelo (lento, 0%) | resposta fixa imediata |
| "você é humano?" | modelo (0%) | resposta fixa (IDENTIDADE) |
| "oi" / "kkkk" | 46M (~5–10 s) | v4 F (~1–2 s) |
| "você lembra meu nome?" | 46M | 46M (mantém) |
| "quem é você?" | 46M | 46M (mantém) |

## O que NÃO muda

- Pesos (v4 / v6-r0)
- Protocolo de crise (`crise.py` continua antes de tudo)
- Decisão de promoção do modelo

## Teste rápido após aplicar o patch

```bash
python -c "import conversa_roteamento as r; print(r.detectar_categoria_zero('você é burro'))"
# -> insulto
python -m unittest testes_conversa_v3d -v
```

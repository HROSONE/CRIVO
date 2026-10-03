"""Pondera operadores/constantes durante SFT; validação continua com CE comum."""
import re


def pesos_vocabulario(tokenizer,fator=4.):
    import torch
    from linguagem_profunda import ESPECIAIS
    especiais={tokenizer.token_to_id(t) for t in ESPECIAIS}
    pesos=torch.ones(tokenizer.get_vocab_size())
    for i in range(len(pesos)):
        texto=tokenizer.decode([i],skip_special_tokens=False)
        if i not in especiais and (re.search(r'[0-9+\-*/%<>=!]',texto) or
                re.search(r'\b(?:filter|map|reduce|some|every|while|for|true|false)\b',texto)):
            pesos[i]=fator
    return pesos


def perda_ponderada(logits,alvos,pesos):
    import torch.nn.functional as F
    perdas=F.cross_entropy(logits.reshape(-1,logits.shape[-1]),alvos.reshape(-1),
        ignore_index=-100,reduction='none').view_as(alvos)
    w=pesos[alvos.clamp_min(0)]*(alvos!=-100)
    if not w.sum():raise ValueError('Lote sem tokens-alvo')
    return (perdas*w).sum()/w.sum()

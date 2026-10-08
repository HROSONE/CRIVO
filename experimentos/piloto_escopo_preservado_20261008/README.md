# Piloto posterior: escopo preservado

Motivado pela regressão de escopo dos dois treinos primários. Não é outro treinamento: usa operação/ponteiros do candidato eventos e escopo do modelo anterior, com o mesmo preparo. A fórmula e o novo painel foram registrados antes das previsões deste piloto; a tentativa nasceu após abrir o teste primário. São duas redes próprias, 5.896.748 parâmetros instanciados. Não usa modelo/API externo.

48 sessões, 222 prefixos, nenhum truncamento. Novas frases e entidades, mesmas regras e autoria; perguntas Compare favorecem a normalização. Não é avaliação independente. O critério exploratório exige melhora geral e ausência de queda em cada evento crítico versus os pesos anteriores com o mesmo preparo. Não é o critério de aprovação primário, e não autoriza chat.

| Condição | Contratos | Sessões completas |
|---|---:|---:|
| anterior | 105/222 (47.3%) | 1/48 |
| eventos | 160/222 (72.1%) | 10/48 |
| escopo_preservado | 162/222 (73.0%) | 11/48 |

| Evento | Anterior | Composição |
|---|---:|---:|
| confirmacao | 5/12 | 5/12 |
| consulta | 1/12 | 4/12 |
| correcao | 26/54 | 51/54 |
| declaracao | 48/48 | 48/48 |
| hipotese | 14/54 | 18/54 |
| retorno | 11/42 | 36/42 |

O critério exploratório passou nesse novo painel, mas **a composição foi rejeitada pelas regressões**. A associação conhecida caiu de 248/400 com os pesos anteriores para 157/400 com a composição. O painel contextual passou de 379/400 para 366/400. O teste primário, já conhecido quando a fórmula foi criada, passou de 290/552 para 331/552; essa comparação é post hoc. Preservar somente a cabeça de escopo não preserva a relação entre os argumentos e o cenário. Nenhum artefato ativo foi alterado.

`resultados/` conserva dados, protocolos prospectivos, previsões brutas/limitadas e diagnóstico dos painéis conhecidos. `verificacao_caderno.json` registra só uma sequência guiada de cinco turnos executada localmente; não é Colab real ou teste independente. Para repetir em uma pasta nova:

```bash
python experimentos/piloto_escopo_preservado_20261008/piloto.py --saida /tmp/piloto-crivo --preparar
python experimentos/piloto_escopo_preservado_20261008/piloto.py --saida /tmp/piloto-crivo --candidato experimentos/escopo_eventos_20261008/eventos/pesos.pt
```

A tentativa seguinte de `retencao_contrastes_20261008` inclui replay da associação anterior (antes ausente), supervisão por contrastes negados e retenção das distribuições do próprio modelo anterior. Este piloto não é recomendado para substituir o modelo anterior.

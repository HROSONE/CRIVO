# Instruções do projeto CRIVO

- Modelos e APIs de terceiros podem ser usados à vontade fora do CRIVO que conversa, para treinamento, geração de dados, avaliação e ferramentas de desenvolvimento. Eles nunca entram no site, no APK ou no chat, e nunca respondem à pessoa, em nenhuma forma. Os pesos que definem o Crivo (arquitetura, tokenizador e pesos próprios) são sempre só do Crivo.
- Quando um modelo de terceiros gerar dados de treino, esses dados ficam numa pasta própria, marcados com a origem (modelo, versão, data e licença) e separados dos dados humanos e dos escritos no projeto. Nenhum resultado pode chamá-los de humanos. Use só modelo cuja licença permita treinar outro modelo com as saídas.
- Quando um modelo de terceiros julgar respostas do Crivo, a nota é relatada como nota do juiz, ao lado da régua própria (casos às cegas, paráfrases, frases reais do criador), e não a substitui: promover pesos para o chat continua exigindo a régua própria.
- Os pesos, o tokenizador e o código de modelos de terceiros nunca entram no repositório nem no pacote do site ou do APK.
- Autorização registrada em 19/10/2026 por Henrique (dono do HROSONE), que alterou a regra anterior de 14/10/2026.
- Bibliotecas de cálculo e infraestrutura, como NumPy e PyTorch, não são modelos e podem apoiar o treinamento e a inferência dos pesos próprios.
- Preserve branches, commits e PRs existentes. Não feche um PR sem mesclá-lo apenas para substituí-lo por uma consolidação.
- Registre resultados experimentais com seus limites. Verificações bem-sucedidas não autorizam promover pesos com aprovação falsa para o chat. Pesos treinados com dados do professor registram quanto do treino veio dele.
- Crise e urgência de saúde (CVV 188, SAMU 192) são respondidas pelo crise.py antes de qualquer modelo.

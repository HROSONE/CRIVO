# Instruções do projeto CRIVO

- Use somente a arquitetura, os tokenizadores e os pesos próprios do Crivo.
- Não baixe, execute ou integre modelos pré-treinados de terceiros nem APIs de modelos externos no CRIVO que conversa (chat, site, APK, PC local). A restrição inclui serviços locais que executam esses modelos. Os pesos que rodam para o usuário são sempre só do Crivo.
- Exceção autorizada pelo criador (14/10/2026), só fora do CRIVO que conversa:
  - **Professor (destilação):** um modelo de terceiros pode gerar dados de treino para os pesos do Crivo. Esses dados ficam numa pasta própria, marcados com a origem (modelo, versão, data e licença) e separados dos dados humanos e dos escritos no projeto. Nenhum resultado pode chamá-los de humanos. Use só modelo cuja licença permita treinar outro modelo com as saídas.
  - **Juiz (avaliação):** um modelo de terceiros pode dar nota a respostas do Crivo. A nota do juiz é relatada como nota do juiz, ao lado da régua própria (casos às cegas, paráfrases, frases reais do criador), e não a substitui: promover pesos para o chat continua exigindo a régua própria.
  - Os pesos, o tokenizador e o código desses modelos nunca entram no repositório nem no pacote do site ou do APK.
- Bibliotecas de cálculo e infraestrutura, como NumPy e PyTorch, não são modelos e podem apoiar o treinamento e a inferência dos pesos próprios.
- Preserve branches, commits e PRs existentes. Não feche um PR sem mesclá-lo apenas para substituí-lo por uma consolidação.
- Registre resultados experimentais com seus limites. Verificações bem-sucedidas não autorizam promover pesos com aprovação falsa para o chat. Pesos treinados com dados do professor registram quanto do treino veio dele.
- Crise e urgência de saúde (CVV 188, SAMU 192) são respondidas pelo crise.py antes de qualquer modelo.

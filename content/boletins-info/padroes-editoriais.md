---
title: "Padrões editoriais"
description: "Como uma edição dos boletins é feita, o que é checado e o que o leitor deve saber."
summary: "padrões editoriais dos boletins"
hidemeta: true
ShowToc: false
---

Este texto descreve o processo real. Ele muda quando o processo muda.

## Como uma edição é feita

1. **Coleta.** Um script lê os feeds públicos listados em [Fontes](/boletins-info/fontes/). O resultado fica num arquivo da execução, com títulos, links e datas. Nos boletins com Cotações, o retrato das cotações é guardado em arquivo separado.
2. **Ranqueamento.** O script remove duplicatas: o mesmo link ou o mesmo fato em fontes diferentes. Filtra por palavras de exclusão e, em cada fonte, por termos obrigatórios. Pontua cada item pelo peso da fonte, pela recência e pelas palavras-chave do tema. Aplica limites por seção e por fonte.
3. **Escrita.** O texto de cada item (título e resumo) vem da fonte. O modelo traduz títulos e resumos que não estejam em português. Ele escreve "Em resumo", "Por que importa", "O que observar" e "Termos". Pode descartar itens que julga irrelevantes, mas mantém um mínimo por seção. Não acrescenta fatos. O modelo não usa ferramentas: não navega, não busca e não acessa o vault.
4. **Checagem.** A checagem confirma que cada fonte listada é citada no texto. Rejeita links que apontam para a página inicial de um site em vez do artigo. Exige que as Cotações (e os Proventos, quando houver) batam exatamente com o retrato feito na coleta. Edição que falha não é publicada.
5. **Publicação.** As edições são geradas em horário programado. Uma pessoa dispara a cópia para o blog e a publicação. Não há revisão item a item.

## O que cada item traz

- Um título, um resumo curto e o número da fonte entre colchetes, que leva à lista de fontes da edição.
- A linha **Por que importa**, que é uma leitura do modelo a partir do item. Ela não é fato novo e também tem fonte.
- Cotações, quando a edição tem a seção, com o horário informado pela fonte.

## Limites

- As edições são geradas automaticamente. Elas podem conter erro, mesmo com a checagem.
- O modelo resume o que as fontes dizem. Ele não verifica o fato no mundo além do que está no retrato.
- Um dia sem notícia relevante gera uma edição curta, ou uma nota de cobertura. Não é preenchimento.

Se encontrar um erro, veja [Correções](/boletins-info/correcoes/).

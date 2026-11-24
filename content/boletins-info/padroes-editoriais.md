---
title: "Padrões editoriais"
description: "Como uma edição dos boletins é feita, o que é checado e o que o leitor deve saber."
summary: "padrões editoriais dos boletins"
hidemeta: true
ShowToc: false
---

Este texto descreve o processo real. Ele muda quando o processo muda.

## Como uma edição é feita

1. **Coleta.** Um script lê os feeds públicos listados em [Fontes](/boletins-info/fontes/) e guarda um retrato (snapshot) de cada item.
2. **Ranqueamento.** O script filtra por palavras de exclusão e por seção, e ordena os itens pela fonte e pela data.
3. **Escrita.** Um modelo de linguagem recebe só os itens selecionados e escreve o resumo, os itens e a linha "Por que importa". O modelo não usa ferramentas: não navega, não busca e não acessa o vault.
4. **Checagem.** Antes de aceitar a edição, o pipeline confere que cada item cita uma fonte da lista do boletim e que as citações entre aspas batem com o retrato guardado. Edição que falha nessa checagem não é publicada.
5. **Publicação.** Uma pessoa revisa o resultado e publica. Nada vai ao ar sem essa etapa.

## O que cada item traz

- Um título, um resumo curto e o número da fonte entre colchetes, que leva à lista de fontes da edição.
- A linha **Por que importa**, que é uma leitura do modelo a partir do item. Ela não é fato novo e também tem fonte.
- Cotações, quando a edição tem a seção, com o horário informado pela fonte.

## Limites

- As edições são geradas automaticamente. Elas podem conter erro, mesmo com a checagem.
- O modelo resume o que as fontes dizem. Ele não verifica o fato no mundo além do que está no retrato.
- Um dia sem notícia relevante gera uma edição curta, ou uma nota de cobertura. Não é preenchimento.

Se encontrar um erro, veja [Correções](/boletins-info/correcoes/).

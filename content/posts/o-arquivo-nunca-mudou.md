---
tags: ["ai-agents", "verification", "self-evolution", "dspy", "prompt-optimization"]
date: "2026-08-18T09:00:00-04:00"
slug: "o-arquivo-nunca-mudou"
title: "O otimizador melhorou o prompt. O arquivo que ele gravou nunca mudou."
description: "Um pipeline de auto-evolução de agentes com cinco camadas de gate, todas verdes, entregando o baseline intocado. E como provar isso quando nenhum dos otimizadores roda."
draft: false
summary: "Um pipeline de auto-evolução de agentes com cinco camadas de gate, todas verdes, entregando o baseline intocado. E como provar isso quando nenhum dos otimizadores roda."
cover:
  image: "/og/o-arquivo-nunca-mudou.png"
  alt: "O otimizador melhorou o prompt. O arquivo que ele gravou nunca mudou."
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
Fui ler um repo de auto-evolução de agentes para aprender a arquitetura. Saí com
um gate novo no meu vault e uma frase que devia estar pregada em toda pipeline
de auto-melhoria: **o otimizador nunca escreveu no arquivo que o pipeline
gravou.**

O repo é o [hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution),
da Nous Research. A proposta é boa: evoluir skills, prompts e descrições de
ferramenta de um agente por otimização de texto — sem GPU, sem treinar pesos, só
mutação de string avaliada por API. Cinco mil stars. Arquitetura documentada em
quarenta kilobytes de plano.

E cinco camadas de guardrail, listadas no README: suíte de testes 100% verde,
limites de tamanho, compatibilidade de cache, preservação semântica, e review
humano obrigatório em PR. Nada de commit direto.

Nenhuma delas impede o que descrevo abaixo — só duas das cinco estão de fato
ligadas. E o arquivo que sai do outro lado é byte a byte igual ao que entrou.

## O mecanismo, que é burro como sempre

A skill vira um módulo do DSPy. O texto da skill é o parâmetro que o otimizador
deveria evoluir:

```python
class SkillModule(dspy.Module):
    def __init__(self, skill_text: str):
        super().__init__()
        self.skill_text = skill_text          # ← o pipeline lê daqui
        self.predictor = dspy.ChainOfThought(self.TaskWithSkill)
```

No fim da otimização, o pipeline extrai o resultado:

```python
evolved_body = optimized_module.skill_text   # ← e grava isto no disco
```

Só que `skill_text` é um atributo comum, atribuído uma única vez no construtor.
Os otimizadores do DSPy não escrevem lá. Escrevem na assinatura do predictor:

```python
pred.signature = pred.signature.with_instructions(candidate[name])
```

Isso vale para os quatro teleprompters que o repo seleciona — GEPA, MIPROv2 e
SIMBA via `with_instructions`, `infer_rules` atribuindo `signature.instructions`
direto. Mesmo alvo, API diferente. Nenhum toca o atributo do módulo.

O resultado: a otimização acontece de verdade, o ganho medido é real, e o
artefato entregue é o original. O pipeline mede uma coisa e escreve outra.

## Por que os gates não pegaram

Esta é a parte que me interessa, e a razão de o artigo existir.

Antes dos gates, vale perguntar por que o bug existe. O PLAN.md do projeto tem
quarenta kilobytes de arquitetura. Diz que o pipeline "mostra o diff do que
mudou" e "commita a versão melhorada". Em nenhum lugar diz de qual campo sai o
texto evoluído. Não foi descuido de quem escreveu `evolved_body =
optimized_module.skill_text` — foi um buraco no documento que deveria ter
fechado essa pergunta antes da primeira linha de código. Plano longo não é
plano preciso: faltou uma frase nomeando o campo, e nenhuma quantidade de
kilobytes cobre isso.

As duas que valem: tamanho compara bytes, crescimento rejeita variante que
inflar mais de 20% sobre o baseline, e ambos bloqueiam o deploy quando falham.
Tem holdout separado — conjunto que o otimizador nunca viu — para detectar
overfit ao juiz. É mais rigor do que a média.

Os outros três são promessa. A preservação semântica não existe no código. A
criação do PR não existe. E o primeiro guardrail do README, "suíte de testes
deve passar 100%" — o que o plano do projeto chama de *the hard floor* — tem a
função escrita, tem a flag `--run-tests` na linha de comando, e **zero chamadas**.
Você passa a flag, o run termina limpo, e conclui que os testes passaram. Nada
rodou.

E todos operam sobre **objetos em memória**. O holdout compara o módulo baseline
com o módulo otimizado, e esses dois de fato diferem: as instructions mudaram.
O delta é honesto. Só não descreve o arquivo.

O gate de tamanho recebe o texto que o pipeline *acha* que evoluiu. Como esse
texto é o baseline, ele passa — está dentro do limite, por definição. O de
crescimento passa pelo mesmo motivo: crescimento zero. **Um artefato que não
mudou passa em todo gate que pergunta "mudou demais?".**

Nenhuma das cinco camadas pergunta a única coisa que teria pegado: *o byte que
eu gravei é diferente do byte que eu li?*

## Provar sem conseguir rodar

Quis confirmar antes de afirmar. Aí veio o segundo problema. Método: commit
`0a929e3aa20e15cf04dc7c28492a7d41a5139125` (2026-06-17), dspy 3.3.0, inspeção
estática do código instalado + reprodução da operação — não execução do
pipeline.

O `pyproject.toml` declara `dspy>=3.0.0`, sem teto. Instalação nova hoje resolve
para 3.3.0, onde a chamada do repo não existe mais:

```
TypeError: GEPA.__init__() got an unexpected keyword argument 'max_steps'
```

O código trata isso com um `except` genérico e cai no MIPROv2 imprimindo
"falling back" — o usuário vê um aviso, não um erro. Ou seja: **o caminho GEPA
do commit analisado não executa numa instalação limpa que resolve para dspy
3.3.0.** E o fallback exige um LM real devolvendo JSON válido, então também não
roda offline. Não existe caminho de verificação barato.

Fiquei sem prova de execução. O reflexo é desistir ou pagar por uma chave de
API. Fiz outra coisa: **provei o mecanismo em vez do fluxo.**

```python
m = SkillModule("## Procedure\n\n1. Read the task.")
before = m.skill_text
for name, pred in m.named_predictors():
    pred.signature = pred.signature.with_instructions("MUTATED BY OPTIMIZER")
print(m.skill_text != before)
```

Dez linhas. Reproduzem literalmente a operação que a biblioteca faz sobre o
candidato — a mesma linha, o mesmo objeto. Sem chave, sem rede, sem depender de
qual versão do otimizador está instalada.

Saída: `False`. O atributo não muda — prova o mecanismo na versão analisada,
não o pipeline inteiro em toda versão.

Prova de mecanismo vale mais que prova de execução, e custa uma fração. Quando
o teste depende de uma biblioteca de terceiros conseguir rodar, você amarrou seu
veredito à saúde da suíte alheia. Reproduzir à mão a operação suspeita não
depende de versão, de chave nem de rede.

## O que eu levei para casa

Meu vault tem cerca de duzentos arquivos de agente e um checador que valida
estrutura, aliases, triggers e contratos. Nenhum olhava tamanho. Portei o gate
de tamanho do repo — a ideia é boa, o crescimento relativo é a parte com dentes:
prompt cresce monotonicamente sob edição incremental, cada ajuste adiciona e
nenhum remove, e um teto absoluto só acusa quando o estrago já está feito. Meu
gate compara contra o `HEAD` do git e rejeita acima de +20%.

Os limites vieram da distribuição real dos meus arquivos, não de um número
bonito: mediana de 5.081 bytes, p90 de 9.512, maior arquivo em 23.190. O corte
duro ficou em 24.000 — acima do que existe hoje. Um gate que reprova o acervo no
dia da estreia não é adotado, é desligado.

E a linha que o repo me ensinou, comentada no código para não se perder:

> Valida o byte que foi para o disco. Nunca um objeto em memória.

O teste que prova isso força o cache de baseline a discordar do git, para
garantir que o cache é de fato consultado. Sem esse negativo plantado, o teste
passaria por acidente caso o caminho rápido fosse ignorado — que é a mesma
classe de erro deste artigo, uma camada acima.

## O que isto não é

Não é um "olha o erro dos outros". O repo se declara Phase 1 de 5, é código de
pesquisa recente, e a arquitetura dele é boa o bastante para eu ter copiado uma
peça. Meu veredito foi *adotar o padrão, não adotar o código* — e o padrão é
mesmo bom: repo-otimizador separado do repo-alvo, artefato de texto como
parâmetro, evoluir primeiro o que é barato de reverter.

Também não rodei o pipeline com um LM pago. O que provei é onde a escrita
aterrissa, que é determinístico e observável sem gastar um centavo. A magnitude
do ganho reportado eu não medi — e nem precisa, porque o ganho é de um artefato
que não é o entregue.

## O que ainda não sei

Se o repo já corrigiu isso. Li o código no estado de 17 de agosto de 2026, e o
último push era de dois meses antes. Um `git pull` amanhã pode invalidar metade
deste artigo — e seria ótimo.

Se uma versão antiga do DSPy mudaria o veredito. Provei o mecanismo contra a
3.3.0 e contra o código dos quatro teleprompters que o repo seleciona hoje. Se
em alguma versão anterior o `compile` copiasse atributos arbitrários do módulo,
o pipeline teria funcionado por acidente numa janela que eu não testei.

Se o ganho transferiria, mesmo com o bug resolvido. O harness de avaliação é uma
única chamada de `ChainOfThought`, sem ferramentas e sem multi-turno — um
simulador do agente, não o agente. Uma skill otimizada contra o simulador pode
não render nada no ambiente real, e essa é uma pergunta separada, mais difícil,
que ninguém responde com dez linhas de probe.

E se meus próprios números prestam. O corte de +20% eu herdei; a mediana e os
percentis são do meu acervo. Não sei se +20% é generoso ou apertado para um
vault com outra forma — só sei que ter *algum* limite relativo é melhor que ter
só um teto absoluto.

Se o meu próprio gate está livre do mesmo defeito. Não mais. `verify-run.sh:512`
agora chama `check-agent-size.py --json --strict`. A flag crua reprovaria 19
arquivos por bloat — `forge.md` (23.190 bytes), `observability.md` (20.377).
Entrou no-regression: `Finding` ganhou o campo `preexisting`; WARN só reprova
o que está ausente do baseline em HEAD — o próprio código cita o precedente,
a emenda `rotina.lint` de 2026-08-13 em `decisions.md`: gate que reprova por
estado alheio ao alvo se desliga, não se obedece. Vault: `ok=true`, 189
arquivos, 0 fail, 22 warn, 0 novo. Regressão plantada em `core/verify.md`
(9.401→9.712 bytes) deu `ok=false, 1 warn (1 novo)`; restaurei, git limpo. O
que não sei: se a varredura pegou todos os casos da família, ou só o que eu
já suspeitava.

## A tese

Auto-evolução tem duas metades e elas não têm o mesmo preço. **Mutar é fácil.
Medir é difícil.** Gerar mil variantes de um prompt é uma tarde. Saber qual
delas é melhor, e provar que foi *aquela* que chegou ao disco, é o trabalho
inteiro.

Um loop de auto-melhoria que mede o artefato errado não falha alto. Ele produz
relatório, delta positivo, gate verde e confiança. É a pior falha possível num
sistema cujo propósito é justamente permitir que você pare de olhar.

Se você está construindo algo que se melhora sozinho, o gate mais barato que
existe é também o que quase ninguém escreve: leia o arquivo depois de gravar, e
compare com o que você leu antes. Se forem iguais, o seu otimizador não fez nada
— por mais verde que esteja o painel.

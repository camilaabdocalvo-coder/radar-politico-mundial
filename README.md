# Radar Político Mundial — MVP de custo mínimo

Este projeto produz, a cada quatro horas, um arquivo JSON com notícias políticas
priorizadas e o publica gratuitamente pelo GitHub Pages. Um GPT personalizado pode
consultar esse arquivo por meio de uma Action.

## O que entra no ranking

- veículos prioritários: Estadão, O Antagonista, Metrópoles, Folha de S.Paulo,
  Brasil Paralelo, Gazeta do Povo e Poder360;
- cobertura internacional via consultas multilíngues do Google News RSS;
- filtro editorial exclusivamente político;
- pontuação por recência, relevância política, prioridade da fonte e repetição do
  mesmo assunto em fontes diferentes.

O MVP **não afirma medir comentários ou acessos do X e Instagram**. Esses números
dependem das APIs oficiais e de suas permissões/planos. Os conectores sociais podem
ser adicionados depois sem alterar a interface usada pelo GPT.

## Publicação gratuita

1. Crie um repositório público no GitHub e envie esta pasta para ele.
2. Em **Settings → Pages**, selecione **Deploy from a branch**, branch `main`, pasta
   `/docs`.
3. Em **Actions**, habilite workflows. O arquivo `.github/workflows/update.yml`
   executará a coleta a cada quatro horas e atualizará `docs/latest.json`.
4. Rode o workflow manualmente uma vez (`Run workflow`).
5. Confira `https://camilaabdocalvo-coder.github.io/radar-politico-mundial/latest.json`.

## Criar o GPT

1. No editor de GPTs, crie um GPT chamado **Radar Político Mundial**.
2. Cole o conteúdo de `gpt/instructions.md` em **Instruções**.
3. Em **Actions**, importe `gpt/openapi.yaml`.
4. Em autenticação, escolha **None**.
5. Use `https://camilaabdocalvo-coder.github.io/radar-politico-mundial/privacy.html`
   como URL da política de privacidade.
6. Teste a Action e compartilhe como **Qualquer pessoa com o link**.

## Rodar localmente

Requer apenas Python 3.11 ou superior:

```bash
python3 collector.py
python3 -m unittest discover -s tests
```

## Limites e evolução social

Para medir engajamento real:

- X: adicionar `X_BEARER_TOKEN` e usar tendências, busca recente e
  `public_metrics` da API oficial;
- Instagram: criar um app Meta e obter acesso compatível com contas profissionais;
  a API não oferece um ranking irrestrito dos posts mais populares de todo o
  Instagram;
- alternativa de custo controlado: contratar uma plataforma licenciada de social
  listening somente depois de validar o valor editorial do MVP.

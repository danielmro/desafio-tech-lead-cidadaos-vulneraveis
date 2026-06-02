# Desafio Técnico - Tech Lead
## Programa Pequenos Cariocas (PIC)

---

## Contexto

O **Programa Pequenos Cariocas** é uma iniciativa intersetorial da Prefeitura do Rio de Janeiro que acompanha crianças de 0 a 6 anos e gestantes em situação de vulnerabilidade, integrando dados de Saúde (SMS), Educação (SME) e Assistência Social (SMAS).

O coração do programa é uma plataforma full-stack composta por um pipeline de dados, uma API e um frontend que permite a gestores e operadores de campo acompanhar indicadores e buscar beneficiários. Como Tech Lead, você será responsável por manter e evoluir todas essas camadas.

Este desafio usa **dados públicos do 1746** no lugar dos dados sensíveis do programa. O objetivo não é reproduzir nossa solução — é ver como você resolve problemas semelhantes com suas próprias escolhas técnicas.

---

## Instruções

1. Crie um **fork público deste repositório** com suas respostas
2.  Documente suas decisões — queremos entender por que você fez cada escolha, não só o que fez
3. Inclua um `README.md` explicando como rodar o projeto localmente

---

## Dados

**`datario.adm_central_atendimento_1746.chamado`** — tabela pública no BigQuery com 14M+ chamados de 2015 a 2024.

Campos relevantes: `id_chamado`, `data_inicio`, `data_fim`, `data_alvo_finalizacao`, `tipo`, `subtipo`, `status`, `situacao`, `longitude`, `latitude`, `data_particao`.

Tabelas auxiliares: `datario.dados_mestres.bairro`, `regiao_administrativa`, `area_planejamento`, `subprefeitura`.

Use o BigQuery apenas para extrair os dados brutos (filtre por `data_particao >= '2023-01-01'`). A partir daí, trabalhe localmente da forma que preferir.

obs.: o campo que era solicitado na demanda original, era o "prazo_atendimento", porém não existe este campo no banco de dados e o mais próximo que encontrei foi o 
"data_alvo_finalizacao", que então substituí no lugar. 

---

## O Desafio

Construa um sistema de monitoramento de chamados do 1746 com as seguintes capacidades:

---

### 1. Documentação técnica

Antes de começar, crie o arquivo `docs/decisoes.md` e vá preenchendo ao longo do desafio. Este documento é o principal entregável para avaliar sua visão de Tech Lead — queremos ver como você pensa, não só o que você construiu.

Cubra:

- **Escolhas tecnológicas**: por que você escolheu cada ferramenta ou abordagem, e o que considerou antes de decidir
- **Tradeoffs e dívida técnica**: o que você deixou de fora ou fez de forma simplificada, por quê, e como priorizaria resolver
- **Padrões e boas práticas**: convenções de código, linting, estrutura de commits, estratégia de testes — o que você estabeleceria se este fosse um projeto real de time
- **Escalabilidade e manutenção**: como o sistema se comporta à medida que cresce, e o que mudaria com mais dados, mais usuários ou mais secretarias

**Entregue**: `docs/decisoes.md` objetivo e direto — não um ensaio, mas um documento que um engenheiro novo no projeto acharia útil.

---

### 2. Pipeline de dados

Use **dbt + DuckDB ou SQLite** para transformar os dados brutos em algo utilizável pela aplicação. Esperamos ver pelo menos uma camada de transformação (limpeza, enriquecimento, colunas derivadas) e uma camada de agregação que sirva o dashboard.

**As agregações que alimentam o dashboard devem ser feitas aqui**, nos modelos dbt — a API não deve recalculá-las a cada requisição.

Uma das colunas que você vai precisar derivar é a secretaria responsável por cada chamado, a partir do campo `tipo`. Explore os valores disponíveis, defina seu critério de mapeamento e documente as decisões — inclusive o que ficou ambíguo.

**Entregue**: modelos dbt funcionando + documentação das decisões de modelagem.

---

### 3. API

Uma API que sirva os dados transformados para o frontend. **Filtragem, busca, ordenação e paginação devem ocorrer aqui** — o frontend não acessa o banco diretamente nem faz operações sobre os dados.

- Listagem de chamados com filtros, busca, ordenação e paginação — a API deve ser paginada; o frontend nunca recebe o dataset completo, exceto na exportação
- Endpoint de dashboard servindo os indicadores já agregados pelos modelos dbt
- Cache: o dataset não deve ser relido da fonte a cada requisição

**Entregue**: API rodando localmente com documentação de como executar.

---

### 4. Frontend

Uma interface que consuma a API e permita:

- Visualizar indicadores do dashboard (volume de chamados, taxa de resolução no prazo, tempo médio de resolução, evolução temporal)
- Buscar e filtrar chamados com filtros em cascata (as opções disponíveis refletem os dados retornados)
- Exportar os dados filtrados

**Entregue**: frontend rodando localmente.

**Sugestão**: Utilize o framework Next.js 14+ (App router).

---

### 5. Autenticação

Implemente o fluxo de autenticação OAuth 2.0 / OIDC integrado a um IdP (pode ser mockado): o fluxo deve cobrir login, validação de token, refresh e logout. O backend deve proteger seus endpoints validando tokens.

**Entregue**: fluxo funcionando end-to-end (pode ser mockado) + documentação de como seria a integração com um provedor real (ex: Keycloak).

---

### 6. Controle de acesso

Projete e implemente um sistema de controle de acesso com hierarquia de roles:

- **operador** — acesso de leitura
- **admin** — acesso de leitura e gestão de operadores
- **super admin** — acesso total, incluindo gestão de admins

Admins não podem conceder permissões acima das que possuem.

**Entregue**: modelagem do controle de acesso + implementação das regras na API + testes das validações de negócio.

---

## Avaliação

Você será avaliado em cada uma das categorias abaixo, com seus respectivos pesos:

- **Engenharia de dados**: peso 1
- **Backend e frontend**: peso 2
- **Documentação e comunicação**: peso 2

Uma média ponderada será calculada e os melhores candidatos serão chamados para a etapa de entrevistas.

**Dica**: procure fazer algo diferente! Devido à grande quantidade de candidatos, é possível que uma boa média não seja suficiente para te garantir uma entrevista. Tente se destacar!

---

## Estrutura Sugerida do Repositório

```
desafio-tech-lead-pic/
├── README.md
├── docs/
│   └── decisoes.md          
├── data/                    # dados exportados do BigQuery (não commitar)
│   └── .gitkeep
├── pipeline/                # dbt project
│   ├── models/
│   │   ├── intermediate/
│   │   └── mart/
│   ├── dbt_project.yml
│   └── profiles.yml.example
├── backend/
│   ├── api/
│   ├── tests/
│   └── README.md            # como rodar
└── frontend/
    ├── app/
    └── README.md            # como rodar
```

---

## FAQ

**Preciso implementar tudo?**
Sim, mas profundidade importa mais do que cobertura — 3 partes muito bem feitas valem mais do que 5 partes superficiais.

**Preciso de acesso ao BigQuery?**
Apenas para extrair os dados uma vez. O dataset `datario` é público — basta ter uma conta Google com o BigQuery habilitado.

**Preciso subir um Keycloak real?**
Não. Mocke a autenticação nos testes. O que avaliamos é o design e a corretude das regras, não a integração com o provedor.

**Posso usar bibliotecas específicas?**
Sim! Sugestões por camada:
- Pipeline: `dbt-core`, `dbt-duckdb` ou `dbt-sqlite`
- Backend: `fastapi`, `polars`, `pyjwt`, `uvicorn`
- Frontend: `next`, `shadcn/ui`, `tailwindcss`, `recharts`, `tanstack/react-query`, `exceljs`

---

## Contato

Dúvidas? Envie um email para **selecao.pcrj@gmail.com**

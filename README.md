# Amazon Listing Automation

Sistema local de automação para criar listagens de produtos na Amazon.com (EUA). Roda como pipeline diário em quatro etapas: pesquisa, curadoria, geração de copy com IA e exportação para upload manual.

## Instalação

```bash
cd amazon-listing-automation
pip install -r requirements.txt
```

## Configuração

Copie o arquivo de exemplo e preencha:

```bash
cp .env.example .env
```

### Opção 1: Ollama (gratuito, local)

Instale o [Ollama](https://ollama.com), inicie o serviço e baixe um modelo:

```bash
ollama serve
ollama pull qwen3.5:2b
```

O `.env` fica assim:

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3.5:2b
```

### Opção 2: API da Anthropic (Claude, pago)

Crie uma chave em [console.anthropic.com](https://console.anthropic.com) → API Keys.

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
```

### Todas as variáveis

| Variável | Obrigatória | Descrição |
|---|---|---|
| `LLM_PROVIDER` | Não | `ollama` (padrão) ou `anthropic` |
| `OLLAMA_MODEL` | Não | Modelo do Ollama. Padrão: `qwen3.5:2b` |
| `OLLAMA_BASE_URL` | Não | URL do Ollama. Padrão: `http://localhost:11434` |
| `ANTHROPIC_API_KEY` | Só com `anthropic` | Chave da API da Anthropic (Claude) |
| `MIN_CURATION_SCORE` | Não | Score mínimo (0–100) para aprovar um produto. Padrão: 60 |
| `MAX_PRODUCTS_PER_RUN` | Não | Máximo de produtos para gerar copy por execução. Padrão: 5 |

## Formato do `candidates.csv`

Preencha o arquivo `data/candidates.csv` com produtos pesquisados manualmente. Use Amazon Best Sellers, Movers & Shakers e Google Trends como fontes.

| Coluna | Tipo | Descrição |
|---|---|---|
| `name` | texto | Nome do produto (identificador único) |
| `category` | texto | Categoria na Amazon (ex: Kitchen, Electronics) |
| `price_usd` | número | Preço de venda pretendido em dólares |
| `competitor_reviews` | inteiro | Quantidade de reviews do principal concorrente |
| `competitor_rating` | número | Nota média (1.0–5.0) dos concorrentes |
| `demand_score` | inteiro | Sua avaliação de demanda de 0 (nenhuma) a 10 (altíssima) |
| `notes` | texto | Anotações livres sobre o produto |

Exemplo:

```csv
name,category,price_usd,competitor_reviews,competitor_rating,demand_score,notes
Silicone Kitchen Utensil Set,Kitchen,24.99,320,3.8,8,Concorrentes com reclamações de qualidade
```

## Execução manual

```bash
python main.py
```

O pipeline roda as quatro etapas em sequência. As listagens prontas são exportadas como JSON em `data/output/`.

Para rodar uma etapa isolada (útil para debug):

```bash
python research.py
python curation.py
python copy_generator.py
python publish.py
```

## Agendamento

**O computador precisa estar ligado no horário agendado.** Se estiver desligado ou em suspensão, a execução não acontece.

### Linux / macOS (cron)

```bash
crontab -e
```

Adicione a linha (exemplo: todo dia às 08:00):

```
0 8 * * * cd /caminho/para/amazon-listing-automation && /usr/bin/python3 main.py >> logs/pipeline.log 2>&1
```

### Windows (Agendador de Tarefas)

1. Abra o **Agendador de Tarefas** (Task Scheduler)
2. Clique em **Criar Tarefa Básica**
3. Defina o gatilho: **Diariamente**, no horário desejado
4. Ação: **Iniciar um programa**
   - Programa: `python` (ou caminho completo, ex: `C:\Python312\python.exe`)
   - Argumentos: `main.py`
   - Iniciar em: `C:\caminho\para\amazon-listing-automation`
5. Marque **"Executar estando o usuário conectado ou não"** se quiser que rode mesmo com a tela bloqueada

## O que muda quando a SP-API for liberada

Quando você tiver conta de vendedor aprovada e credenciais da Amazon SP-API:

1. Adicione `SP_API_REFRESH_TOKEN`, `SP_API_CLIENT_ID` e `SP_API_CLIENT_SECRET` ao `.env`
2. Implemente `publish_via_sp_api()` em `publish.py` (o esqueleto com os passos já está lá)
3. O restante do pipeline não precisa mudar — o fluxo de pesquisa, curadoria e copy é o mesmo

Da mesma forma, quando tiver assinatura de Jungle Scout ou Helium 10:

1. Substitua a função `load_candidates()` em `research.py` por uma chamada à API
2. Nenhum outro módulo é afetado

Para trocar de Ollama para Claude, basta alterar `LLM_PROVIDER=anthropic` no `.env` e preencher a `ANTHROPIC_API_KEY`.

## Estrutura de arquivos

```
├── main.py              # Orquestrador do pipeline
├── config.py            # Carrega e valida configuração
├── storage.py           # Camada de persistência (SQLite)
├── research.py          # Etapa 1: leitura de candidatos
├── curation.py          # Etapa 2: scoring e filtragem
├── copy_generator.py    # Etapa 3: geração de copy com Claude
├── publish.py           # Etapa 4: exportação para revisão
├── data/
│   ├── candidates.csv          # Seus candidatos (editável)
│   ├── candidates_example.csv  # Exemplo de referência
│   └── output/                 # JSONs exportados
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

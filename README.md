# Pipeline Automatizado de Extração, Classificação e Governança Documental (LLM + Python)

Pipeline de **Automação Inteligente de Processos (IPA)** desenvolvido em Python para transformar textos brutos não estruturados em bases de conhecimento JSON padronizadas, auditáveis e prontas para consumo em aplicações web ou analíticas.

O projeto substitui processos manuais de triagem, categorização e cadastro por um fluxo automatizado com **validação estrita de schema (Pydantic)**, **classificação baseada em taxonomia controlada**, **detecção de duplicidade** e **promoção segura entre ambientes de *Staging* e *Produção***.

---

## Arquitetura do Fluxo (Ponta a Ponta)

```text
┌──────────────────────┐      ┌─────────────────────────────────────┐      ┌──────────────────────────┐
│   raw_input.txt      │─────▶│  Agente Extrator & Classificador    │─────▶│  historico_brutas/       │
│  (Texto Bruto)       │      │  (LangChain + Gemini + Pydantic)    │      │  (Backup c/ Timestamp)   │
└──────────────────────┘      └──────────────────┬──────────────────┘      └──────────────────────────┘
                                                 │
                                                 ▼
┌──────────────────────┐      ┌─────────────────────────────────────┐      ┌──────────────────────────┐
│  production_items    │◀─────│  Publicador & Controle de IDs       │◀─────│  staging_items.json      │
│  (Base Oficial JSON) │      │  (publicar_questoes.py)             │      │  + Validador Duplicidade │
└──────────────────────┘      └─────────────────────────────────────┘      └──────────────────────────┘
```

1. **Ingestão:** O texto não estruturado é depositado no arquivo de entrada (`raw_input.txt`).
2. **Extração & Classificação (`main_provas.py` / `main_ineditas.py`):** O agente interpreta o texto via LLM, aplica regras de limpeza e mapeia cada registro estritamente para uma categoria autorizada em `taxonomy.md`.
3. **Rastreabilidade de Lote:** Cada registro recebe um identificador único (`UUIDv4`) e é gravado na camada intermediária (`data/staging_items.json`). O arquivo bruto original é movido automaticamente para `historico_brutas/` com *timestamp* e limpo para o próximo ciclo.
4. **Quality Gate / Deduplicação (`validar_duplicadas.py`):** Antes da publicação, o script calcula a similaridade textual (TF-IDF + Similaridade de Cosseno) dentro do próprio *staging* e contra toda a base de produção para alertar sobre registros redundantes.
5. **Promoção para Produção (`publicar_questoes.py`):** Transfere apenas os registros inéditos para o JSON final de produção, previne colisões de UUID e reseta o arquivo de *staging*.

---

## Estrutura do Projeto

```text
├── data/                        # Bases locais em JSON (ignorado no Git)
│   ├── staging_items.json       # Área intermediária de validação
│   └── production_items.json    # Base consolidada final
├── historico_brutas/            # Arquivo histórico de lotes processados (ignorado no Git)
├── samples/                     # Exemplos genéricos para demonstração e testes
│   └── raw_input_exemplo.txt
├── instrucoes_provas.md         # System prompt para extração de documentos históricos
├── instrucoes_ineditas.md       # System prompt para estruturação de registros sintéticos
├── taxonomy.md                  # Lista controlada de domínios e tópicos autorizados
├── main_provas.py               # Pipeline de extração com metadados de origem
├── main_ineditas.py             # Pipeline de extração para novos registros
├── validar_duplicadas.py        # Auditoria de similaridade textual (Staging vs. Produção)
├── publicar_questoes.py         # Promoção de registros validados e limpeza do staging
├── requirements.txt             # Dependências do projeto
├── .env.example                 # Modelo de variáveis de ambiente
└── .gitignore                   # Proteção de chaves, ambientes virtuais e dados locais
```

---

## Diferenciais de Engenharia & Governança

* **Contrato de Dados Garantido (*Schema Enforcement*):** Uso de `Pydantic` combinado ao `JsonOutputParser` do LangChain para assegurar que a saída do modelo respeite rigorosamente os tipos e campos esperados antes de tocar o sistema de arquivos.
* **Prevenção de Alucinação Categorial:** O prompt injeta dinamicamente a lista fechada de `taxonomy.md`, proibindo o modelo de criar, abreviar ou alterar categorias fora do padrão corporativo.
* **Arquitetura Desacoplada por Ambiente:** Todos os caminhos de entrada, prompts, taxonomia e destino de produção são configuráveis via variáveis de ambiente (`.env`), permitindo integrar a saída diretamente a aplicações externas (como front-ends em React ou pipelines de dados) sem alterar o código-fonte.
* **Idempotência na Publicação:** A verificação por `UUID` impede duplicação acidental de registros na base final mesmo em caso de reexecução do script de publicação.

---

## Como Executar Localmente

### 1. Clone o repositório e configure o ambiente virtual

```bash
git clone https://github.com/Lcapp29/llm-pipeline-questoes-card.git
cd llm-pipeline-questoes-card

python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto a partir do `.env.example` e insira sua chave de API do Google Gemini:

```env
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash

# Opcionais (valores padrão abaixo)
TAXONOMY_FILE=taxonomy.md
RAW_INPUT_FILE=raw_input.txt
PRODUCTION_JSON_PATH=data/production_items.json
```

### 3. Execute o fluxo de ponta a ponta

1. Copie o conteúdo de `samples/raw_input_exemplo.txt` para `raw_input.txt`.
2. Rode o extrator para gerar os registros estruturados no *staging*:
   ```bash
   python main_provas.py
   ```
3. Execute a auditoria de similaridade para verificar duplicidades:
   ```bash
   python validar_duplicadas.py
   ```
4. Promova os registros validados para a base oficial de produção:
   ```bash
   python publicar_questoes.py
   ```

---

## Autor

**Lucas de Andrade Cappola** — Engenheiro de Produção | Processos, BPM & Automação  
[LinkedIn](https://www.linkedin.com/in/lucas-cappola) • [GitHub](https://github.com/Lcapp29)
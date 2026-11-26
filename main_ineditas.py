import json
import os
import shutil
import uuid
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, os.getenv("PROMPT_SYNTHETIC_FILE", "instrucoes_ineditas.md"))
TAXONOMY_PATH = os.path.join(BASE_DIR, os.getenv("TAXONOMY_FILE", "taxonomy.md"))
RAW_INPUT_PATH = os.path.join(BASE_DIR, os.getenv("RAW_INPUT_FILE", "raw_input.txt"))
STAGING_PATH = os.path.join(BASE_DIR, "data", "staging_items.json")


class ItemEstruturado(BaseModel):
    disciplina: str = Field(description="Domínio principal em maiúsculas, ex: GESTÃO DE PROCESSOS")
    topico_edital: str = Field(description="Tópico exato da taxonomia correspondente. DEVE estar na lista autorizada.")
    pergunta: str = Field(description="Enunciado ou assertiva limpa e formatada")
    gabarito: str = Field(description="Validação estritamente como 'CERTO' ou 'ERRADO'")
    comentario: str = Field(description="Fundamentação técnica da resposta, excluindo CERTO ou ERRADO do início")


class ListaItens(BaseModel):
    questoes: list[ItemEstruturado] = Field(description="Lista contendo todos os registros extraídos")


with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    template_instrucoes = f.read()

with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
    texto_taxonomia = f.read()

if not os.path.exists(RAW_INPUT_PATH) or os.path.getsize(RAW_INPUT_PATH) == 0:
    print(f"O arquivo '{os.path.basename(RAW_INPUT_PATH)}' está vazio. Nada a processar.")
    exit()

with open(RAW_INPUT_PATH, "r", encoding="utf-8") as f:
    texto_bruto = f.read()

llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

parser = JsonOutputParser(pydantic_object=ListaItens)

prompt = ChatPromptTemplate.from_messages([
    ("system", template_instrucoes + "\n\nINSTRUÇÕES DE FORMATAÇÃO OBRIGATÓRIAS:\n{format_instructions}"),
    ("user", "Extraia e classifique os registros do seguinte texto bruto:\n\n{texto_bruto}")
])

print("Enviando texto para extração estruturada via LLM...")
prompt_formatado = prompt.format_messages(
    taxonomia_autorizada=texto_taxonomia,
    texto_bruto=texto_bruto,
    format_instructions=parser.get_format_instructions()
)

resposta_bruta = llm.invoke(prompt_formatado)

conteudo_texto = resposta_bruta.content
if isinstance(conteudo_texto, list):
    conteudo_texto = str(conteudo_texto)

if not conteudo_texto.strip():
    print("\n[ERRO CRÍTICO] O modelo devolveu uma resposta vazia.")
    exit()

print("\nResposta recebida. Iniciando validação do JSON...")
try:
    resultado = parser.invoke(resposta_bruta)
except Exception:
    print(f"\n[ERRO DE FORMATAÇÃO] Falha ao extrair JSON:\n{conteudo_texto}")
    exit()

os.makedirs(os.path.dirname(STAGING_PATH), exist_ok=True)

dados_existentes = {"questoes": []}
if os.path.exists(STAGING_PATH):
    with open(STAGING_PATH, "r", encoding="utf-8") as f:
        try:
            dados_existentes = json.load(f)
        except json.JSONDecodeError:
            pass

novos_itens = resultado["questoes"]

for item in novos_itens:
    item["id"] = str(uuid.uuid4())
    item["prova"] = "sintético"

dados_existentes["questoes"].extend(novos_itens)

with open(STAGING_PATH, "w", encoding="utf-8") as f:
    json.dump(dados_existentes, f, ensure_ascii=False, indent=2)

print(f"Sucesso! {len(novos_itens)} novos registros adicionados ao staging.")

pasta_historico = os.path.join(BASE_DIR, "historico_brutas")
os.makedirs(pasta_historico, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.move(RAW_INPUT_PATH, os.path.join(pasta_historico, f"lote_{timestamp}.txt"))
with open(RAW_INPUT_PATH, "w", encoding="utf-8") as f:
    f.write("")
print(f"Arquivo '{os.path.basename(RAW_INPUT_PATH)}' limpo e arquivado no histórico!")
import json
import os
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STAGING_PATH = os.path.join(BASE_DIR, "data", "staging_items.json")
FINAL_PATH = os.getenv(
    "PRODUCTION_JSON_PATH",
    os.path.join(BASE_DIR, "data", "production_items.json"),
)

LIMIAR_SIMILARIDADE = 0.75


def carregar_staging(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
            if isinstance(dados, dict):
                return dados.get("questoes", [])
            elif isinstance(dados, list):
                return dados
        except json.JSONDecodeError:
            return []
    return []


def carregar_final(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
            return dados if isinstance(dados, list) else []
        except json.JSONDecodeError:
            return []


def verificar_duplicadas():
    staging = carregar_staging(STAGING_PATH)
    final = carregar_final(FINAL_PATH)

    if not staging:
        print(f"⚠️ O arquivo {os.path.basename(STAGING_PATH)} está vazio.")
        return

    print(f"📊 Analisando {len(staging)} registros no Staging contra:")
    print(f"   - O próprio Staging ({len(staging)} itens)")
    print(f"   - A Base de Produção ({len(final)} itens)\n")

    alertas = 0

    if len(staging) > 1:
        textos_staging = [q.get("pergunta", "") for q in staging]
        vectorizer = TfidfVectorizer().fit_transform(textos_staging)
        matriz_sim = cosine_similarity(vectorizer)

        for i in range(len(staging)):
            for j in range(i + 1, len(staging)):
                sim = matriz_sim[i][j]
                if sim >= LIMIAR_SIMILARIDADE:
                    alertas += 1
                    print(f"🚨 [ALERTA STAGING vs STAGING] Similaridade: {sim:.2%}")
                    print(f"   Registro A ({staging[i].get('id')}): {staging[i].get('pergunta','')[:80]}...")
                    print(f"   Registro B ({staging[j].get('id')}): {staging[j].get('pergunta','')[:80]}...")
                    print("-" * 70)

    if final:
        textos_final = [q.get("pergunta", "") for q in final]
        textos_staging = [q.get("pergunta", "") for q in staging]

        vectorizer = TfidfVectorizer().fit([*textos_final, *textos_staging])
        matrix_final = vectorizer.transform(textos_final)
        matrix_staging = vectorizer.transform(textos_staging)

        matriz_sim = cosine_similarity(matrix_staging, matrix_final)

        for i, q_stage in enumerate(staging):
            for j, q_final in enumerate(final):
                sim = matriz_sim[i][j]
                if sim >= LIMIAR_SIMILARIDADE:
                    alertas += 1
                    print(f"🚨 [ALERTA STAGING vs PRODUÇÃO] Similaridade: {sim:.2%}")
                    print(f"   Novo em Staging ({q_stage.get('id')}): {q_stage.get('pergunta','')[:80]}...")
                    print(f"   Existente em Produção ({q_final.get('id')}): {q_final.get('pergunta','')[:80]}...")
                    print("-" * 70)

    if alertas == 0:
        print("✅ Nenhum registro duplicado ou semanticamente similar foi encontrado!")
    else:
        print(f"\n⚠️ Total de {alertas} alerta(s) de duplicidade.")


if __name__ == "__main__":
    verificar_duplicadas()
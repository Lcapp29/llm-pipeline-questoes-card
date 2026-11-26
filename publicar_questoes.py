import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STAGING_PATH = os.path.join(BASE_DIR, "data", "staging_items.json")
FINAL_PATH = os.getenv(
    "PRODUCTION_JSON_PATH",
    os.path.join(BASE_DIR, "data", "production_items.json"),
)


def publicar():
    if not os.path.exists(STAGING_PATH):
        print(f"⚠️  {os.path.basename(STAGING_PATH)} não existe.")
        return

    with open(STAGING_PATH, "r", encoding="utf-8") as f:
        try:
            staging_raw = json.load(f)
        except json.JSONDecodeError:
            staging_raw = {}

    if isinstance(staging_raw, dict):
        novos_itens = staging_raw.get("questoes", [])
    elif isinstance(staging_raw, list):
        novos_itens = staging_raw
    else:
        novos_itens = []

    if not novos_itens:
        print(f"⚠️ Nenhum registro encontrado em {os.path.basename(STAGING_PATH)} para publicar.")
        return

    final_data = []
    if os.path.exists(FINAL_PATH):
        with open(FINAL_PATH, "r", encoding="utf-8") as f:
            try:
                final_data = json.load(f)
            except json.JSONDecodeError:
                final_data = []

    ids_existentes = {
        q.get("id") for q in final_data if isinstance(q, dict) and "id" in q
    }
    itens_para_adicionar = []
    ignorados = 0

    for q in novos_itens:
        if q.get("id") in ids_existentes:
            ignorados += 1
        else:
            itens_para_adicionar.append(q)

    if not itens_para_adicionar:
        print("❌ Todos os registros do staging já existem na base de produção.")
        return

    final_data.extend(itens_para_adicionar)
    os.makedirs(os.path.dirname(FINAL_PATH), exist_ok=True)
    with open(FINAL_PATH, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    with open(STAGING_PATH, "w", encoding="utf-8") as f:
        json.dump({"questoes": []}, f, ensure_ascii=False, indent=2)

    print(
        f"🚀 Sucesso! {len(itens_para_adicionar)} registro(s) adicionado(s) em '{os.path.basename(FINAL_PATH)}'."
    )
    if ignorados > 0:
        print(f"⚠️ {ignorados} registro(s) ignorado(s) por ID repetido.")
    print(
        f"🧹 {os.path.basename(STAGING_PATH)} foi resetado. Total em produção: {len(final_data)} registros."
    )


if __name__ == "__main__":
    publicar()
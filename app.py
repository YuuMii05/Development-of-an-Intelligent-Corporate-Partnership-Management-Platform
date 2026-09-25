from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
from sse_starlette.sse import EventSourceResponse
import ollama
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Partner Matching Engine")

# Only the static/ folder is public (never the project root, which holds .env)
app.mount("/static", StaticFiles(directory="static"), name="static")

ollama_client = ollama.AsyncClient()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL / SUPABASE_SERVICE_KEY in .env")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_local_embedding(text: str):
    response = await ollama_client.embeddings(model="nomic-embed-text", prompt=text)
    return response["embedding"]

@app.get("/stream-match")
async def stream_match(query: str):
    async def event_generator():
        try:
            MATCH_THRESHOLD = 0.30  
            MATCH_COUNT = 3

            # 1. Génération du vecteur et recherche par similarité dans Supabase
            query_vector = await get_local_embedding(query)

            result = await asyncio.to_thread(lambda: supabase.rpc("match_partners", {
                "query_embedding": query_vector,
                "match_threshold": MATCH_THRESHOLD,
                "match_count": MATCH_COUNT
            }).execute())
            
            # Only real partner data is sent to the browser (older rows may still hold demo metric columns)
            real_fields = ("id", "company_name", "industry", "objectives", "similarity")
            matches = [{k: m.get(k) for k in real_fields} for m in (result.data or [])]
            
            # --- LIGNE DE DÉBOGAGE : Regardez votre terminal VS Code pour voir la structure ---
            print("DONNÉES SUPABASE REÇUES :", matches)
            
            # 2. Envoi des données des partenaires à l'interface
            yield {
                "event": "initial_matches",
                "data": json.dumps({"matches": matches})
            }
            
            # 3. Génération des diagnostics d'alignement par l'IA en streaming (uniquement à partir de données réelles)
            for idx, partner in enumerate(matches):
                industry = partner.get("industry") or "Unknown"
                objectives = partner.get("objectives") or industry
                similarity = partner.get("similarity")
                match_pct = f"{round(similarity * 100)}%" if similarity is not None else "unknown"

                prompt_strategique = f"""
        You are an enterprise strategy expert for Huawei.
        Analyze the strategic alignment between the partner '{partner.get('company_name', 'Unknown')}' and the customer requirement: '{query}'.

        PARTNER PROFILE (the only facts you may use):
        - Industry: {industry}
        - Core Capabilities: {objectives}
        - Semantic match with the requirement: {match_pct}

        Write a brief, high-impact alignment diagnostic (exactly 3-4 sentences) explaining which of the partner's capabilities fit the requirement and any capability gaps.
        STRICT RULES: Write exclusively in English. Use only the facts listed above. Do NOT invent any figures, scores, revenue, risk levels or trends. Do not make an introduction, start speaking directly.
        """

                response_stream = await ollama_client.generate(
                    model="llama3",
                    prompt=prompt_strategique,
                    options={"temperature": 0.2}, # Température baissée pour éviter que l'IA hallucine ou invente des chiffres
                    stream=True
                )

                async for chunk in response_stream:
                    text_chunk = chunk.get("response", "")
                    if text_chunk:
                        yield {
                            "event": "ai_chunk",
                            "data": json.dumps({"partner_index": idx, "text": text_chunk})
                        }
            
            yield {"event": "done", "data": "finished"}
        except Exception as e:
            print(f"Erreur dans stream_match: {str(e)}")
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())


# Servir l'interface utilisateur
@app.get("/", response_class=FileResponse)
def home():
    return "index.html"


# Automatisation de la proposition commerciale
@app.post("/generate-proposal")
async def generate_proposal(request: Request):
    data = await request.json()
    partner_name = data.get("partner_name")
    query_requirements = data.get("query_requirements")
    
    prompt = f"""
    Write a formal, short, and highly persuasive B2B partnership proposal letter between Huawei and the company {partner_name}.
    The partnership proposal must be strictly focused on the following client requirement: '{query_requirements}'.
    
    Structure the document clearly:
    1. Formal Corporate Header / Introduction
    2. Shared Strategic Collaboration Objectives
    3. Professional Next-Steps Conclusion
    
    ⚠️ YOU MUST WRITE EXCLUSIVELY IN ENGLISH. Do not include any French text. Specify clearly that this is an official infrastructure deployment initiative.
    Do not invent any figures, prices, dates, statistics or scores.
    """
    
    response = await ollama_client.generate(model="llama3", prompt=prompt)
    return {"proposal": response["response"]}
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client
from sse_starlette.sse import EventSourceResponse
import ollama
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Partner Matching Engine")

# Montage propre des fichiers statiques
app.mount("/static", StaticFiles(directory="."), name="static")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL / SUPABASE_SERVICE_KEY in .env")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class SearchRequest(BaseModel):
    query: str

def get_local_embedding(text: str):
    response = ollama.embeddings(model="nomic-embed-text", prompt=text)
    return response["embedding"]

@app.get("/stream-match")
async def stream_match(query: str):
    async def event_generator():
        try:
            MATCH_THRESHOLD = 0.30  
            MATCH_COUNT = 3

            # 1. Génération du vecteur et recherche par similarité dans Supabase
            query_vector = get_local_embedding(query)
            
            result = supabase.rpc("match_partners", {
                "query_embedding": query_vector,
                "match_threshold": MATCH_THRESHOLD,
                "match_count": MATCH_COUNT
            }).execute()
            
            matches = result.data or []
            
            # --- LIGNE DE DÉBOGAGE : Regardez votre terminal VS Code pour voir la structure ---
            print("DONNÉES SUPABASE REÇUES :", matches)
            
            # 2. Envoi des données des partenaires à l'interface
            yield {
                "event": "initial_matches",
                "data": json.dumps({"matches": matches})
            }
            
            # 3. Génération des diagnostics de santé par l'IA en streaming
            for idx, partner in enumerate(matches):
                # Correction : On s'assure de lire les clés exactes de Supabase (cf. image_23defc.png)
                health = partner.get("health_score", 99) 
                risk = partner.get("risk_level", "Unknown")
                trend = partner.get("engagement_trend", "Unknown")
                value = partner.get("future_value_estimate", "Unknown")
                objectives = partner.get("objectives", partner.get("industry", "")) # fallback sur industry si vide

                # On force l'IA à utiliser STRICTEMENT ces valeurs de Supabase sans traduire en Français
                prompt_strategique = f"""
        You are an enterprise strategy expert for Huawei.
        Analyze the strategic alignment between the partner '{partner.get('company_name', 'Unknown')}' and the customer requirement: '{query}'.
        
        CRITICAL REAL-TIME PARTNER METRICS (You MUST explicitly mention these exact values):
        - Partnership Health Score: {health}/100
        - Risk Level: {risk}
        - Engagement Trend: {trend}
        - Future Value Estimate: {value}
        - Core Capabilities: {objectives}
        
        Write a brief, high-impact alignment diagnostic (exactly 3-4 sentences).
        CRITICAL REGULATION: WRITE EXCLUSIVELY IN ENGLISH. Do not translate trends or risk levels. Keep the exact terms provided above. Do not make an introduction, start speaking directly.
        """
                
                response_stream = ollama.generate(
                    model="llama3",
                    prompt=prompt_strategique,
                    options={"temperature": 0.2}, # Température baissée pour éviter que l'IA hallucine ou invente des chiffres
                    stream=True
                )
                
                for chunk in response_stream:
                    text_chunk = chunk.get("response", "")
                    if text_chunk:
                        yield {
                            "event": "ai_chunk",
                            "data": json.dumps({"partner_index": idx, "text": text_chunk})
                        }
                        await asyncio.sleep(0.01)
            
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
    """
    
    response = ollama.generate(model="llama3", prompt=prompt)
    return {"proposal": response["response"]}
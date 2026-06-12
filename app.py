from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client
from sse_starlette.sse import EventSourceResponse
import ollama
import json
import asyncio
import os

app = FastAPI(title="AI Partner Matching Engine")

# Mount directory assets cleanly
app.mount("/static", StaticFiles(directory="."), name="static")

SUPABASE_URL = "https://cskdqrevtxpxelebsfon.supabase.co"
SUPABASE_KEY = "sb_secret_scosd72di7ezlGQINP3h0A_tc0QB20G"
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

            query_vector = get_local_embedding(query)
            result = supabase.rpc("match_partners", {
                "query_embedding": query_vector,
                "match_threshold": MATCH_THRESHOLD,
                "match_count": MATCH_COUNT
            }).execute()
            
            matches = result.data or []
            
            yield {
                "event": "initial_matches",
                "data": json.dumps({"matches": matches})
            }
            
            for idx, partner in enumerate(matches):
                prompt = f'''
                You are an expert B2B strategic partnership consultant.
                Analyze the alignment between a user's request and a partner company's objectives.
                
                User Request: "{query}"
                Partner Company: "{partner['company_name']}"
                Partner Objectives: "{partner['objectives']}"
                
                Write a brief, precise, 2-sentence justification explaining EXACTLY why this company is a great match based on shared goals or capabilities. Do not use filler text or introductions. Start speaking directly.
                '''
                
                response_stream = ollama.generate(
                    model="llama3",
                    prompt=prompt,
                    options={"temperature": 0.3},
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
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())

# Fast serving of the clean standalone interface file
@app.get("/", response_class=FileResponse)
def home():
    return "index.html"
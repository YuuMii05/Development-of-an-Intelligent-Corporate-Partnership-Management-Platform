from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles  # <-- Added missing import
from pydantic import BaseModel
from supabase import create_client, Client
from sse_starlette.sse import EventSourceResponse
import ollama
import json
import asyncio

app = FastAPI(title="AI Partner Matching Engine")

# <-- Added StaticFiles mount so FastAPI can serve logo.jpg from your directory
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
            MATCH_THRESHOLD = 0.50  
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
                prompt = f"""
                You are an expert B2B strategic partnership consultant.
                Analyze the alignment between a user's request and a partner company's objectives.
                
                User Request: "{query}"
                Partner Company: "{partner['company_name']}"
                Partner Objectives: "{partner['objectives']}"
                
                Write a brief, precise, 2-sentence justification explaining EXACTLY why this company is a great match based on shared goals or capabilities. Do not use filler text or introductions. Start speaking directly.
                """
                
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

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Huawei Cloud Matchmaker</title>
        <style>
            :root {
                --brand-red: #e60012;        
                --tech-black: #111111;       
                --card-bg: rgba(255, 255, 255, 0.7);          
                --text-body: #222224;        
                --text-muted: #6e6e73;       
                --glass-border: rgba(220, 224, 232, 0.65);      
                --bg-main: #f4f6fa;          
            }

            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100vh;
                overflow: hidden;
                font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                background-color: var(--bg-main);
                color: var(--text-body);
            }

            body {
                display: flex;
                flex-direction: column;
                align-items: center;
                box-sizing: border-box;
                position: relative;
            }

            /* Translucent fading background graphics fixed at the bottom */
            .bottom-bg-graphic {
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 45vh;
                background-image: url('/static/lp1.jpg');
                background-size: cover;
                background-position: center bottom;
                background-repeat: no-repeat;
                opacity: 0.25;
                z-index: 1;
                pointer-events: none;
                -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%);
                mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%);
            }

            .top-navbar {
                width: 100%;
                height: 80px;
                background: rgba(255, 255, 255, 0.6);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                display: flex;
                align-items: center;
                padding: 0 40px;
                box-sizing: border-box;
                border-bottom: 1px solid var(--glass-border);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
                z-index: 100;
            }

            .logo-link {
                display: flex;
                align-items: center;
                height: 70px;
                cursor: pointer;
                text-decoration: none;
            }

            .brand-logo-img {
                height: 100%;
                width: auto;
                object-fit: contain;
            }

            .container { 
                width: 100%; 
                max-width: 800px;
                height: calc(100vh - 80px);
                display: flex;
                flex-direction: column;
                padding: 40px 20px 20px 20px;
                box-sizing: border-box;
                z-index: 2;
                position: relative;
            }

            .brand-header {
                text-align: center;
                margin-bottom: 30px;
                flex-shrink: 0;
            }

            h1 { 
                font-size: 2.1rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: var(--tech-black); 
                margin: 0 0 6px 0; 
            }

            h1 span {
                color: var(--brand-red);
            }

            p.subtitle { 
                color: var(--text-muted); 
                font-size: 0.95rem;
                margin: 0;
            }

            .search-wrapper {
                position: relative;
                width: 100%;
                flex-shrink: 0;
                z-index: 10;
            }

            .search-box { 
                display: flex; 
                background: rgba(255, 255, 255, 0.85);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                padding: 6px; 
                border-radius: 40px; 
                border: 1px solid var(--glass-border);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.04);
                transition: all 0.3s ease;
            }

            .search-box:focus-within {
                border-color: rgba(230, 0, 18, 0.35);
                box-shadow: 0 10px 25px rgba(230, 0, 18, 0.06);
                background: #ffffff;
            }

            input { 
                flex: 1; 
                padding: 12px 20px; 
                border: none;
                background: transparent; 
                color: var(--tech-black); 
                font-size: 15.5px; 
                outline: none;
            }

            button { 
                background: var(--tech-black); 
                color: white; 
                border: none; 
                padding: 0 28px; 
                border-radius: 30px;
                font-weight: 600; 
                cursor: pointer; 
                font-size: 13.5px; 
                transition: all 0.2s ease; 
            }

            button:hover { 
                background: var(--brand-red); 
                box-shadow: 0 4px 12px rgba(230, 0, 18, 0.25);
            }

            .suggestions-panel {
                position: absolute;
                top: 115%;
                left: 10px;
                right: 10px;
                background: rgba(255, 255, 255, 0.94);
                backdrop-filter: blur(25px);
                -webkit-backdrop-filter: blur(25px);
                border-radius: 20px;
                border: 1px solid var(--glass-border);
                box-shadow: 0 15px 35px rgba(0,0,0,0.05);
                overflow: hidden;
                opacity: 0;
                transform: translateY(-8px);
                pointer-events: none;
                transition: all 0.25s ease;
            }

            .suggestions-panel.visible {
                opacity: 1;
                transform: translateY(0);
                pointer-events: auto;
            }

            .suggestions-title {
                padding: 14px 20px 8px 20px;
                font-size: 10.5px;
                font-weight: 700;
                text-transform: uppercase;
                color: var(--brand-red);
                letter-spacing: 0.05em;
                border-bottom: 1px solid rgba(0,0,0,0.03);
            }

            .suggestion-item {
                padding: 12px 20px;
                font-size: 13.5px;
                color: #333;
                cursor: pointer;
                transition: all 0.15s ease;
                border-bottom: 1px solid rgba(0,0,0,0.02);
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .suggestion-item:last-child { border-bottom: none; }

            .suggestion-item:hover {
                background-color: rgba(230, 0, 18, 0.03);
                color: var(--brand-red);
                padding-left: 26px;
            }

            .results-list { 
                margin-top: 25px; 
                flex: 1;
                overflow-y: auto;
                padding-right: 4px;
                display: flex; 
                flex-direction: column; 
                gap: 20px; 
                box-sizing: border-box;
            }

            .results-list::-webkit-scrollbar {
                width: 6px;
            }
            .results-list::-webkit-scrollbar-track {
                background: transparent;
            }
            .results-list::-webkit-scrollbar-thumb {
                background: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
            .results-list::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 0, 0, 0.2);
            }

            .card { 
                background: var(--card-bg); 
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                padding: 28px; 
                border-radius: 20px;
                border: 1px solid var(--glass-border);
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.015);
                transition: all 0.25s ease;
            }

            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.03);
                border-color: rgba(230, 0, 18, 0.12);
            }

            .card-header { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 12px; 
            }

            .company-name { 
                font-size: 1.3rem; 
                font-weight: 600; 
                color: var(--tech-black); 
            }

            .badge { 
                background: var(--brand-red); 
                color: #ffffff; 
                padding: 5px 14px; 
                font-size: 0.8rem; 
                font-weight: 700; 
                border-radius: 30px;
            }

            .industry { 
                font-size: 11px; 
                font-weight: 700;
                color: var(--brand-red); 
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 14px; 
            }

            .objectives { 
                color: #444448; 
                line-height: 1.65; 
                font-size: 14.5px;
                margin-bottom: 20px;
            }

            .xai-justification {
                background: rgba(244, 246, 250, 0.65);
                border-radius: 12px;
                border-left: 4px solid var(--brand-red);
                padding: 14px 18px;
                font-size: 14px;
                line-height: 1.6;
                color: #3a3a3e;
            }

            .xai-title {
                font-size: 9.5px;
                font-weight: 800;
                text-transform: uppercase;
                color: var(--brand-red);
                letter-spacing: 0.08em;
                margin-bottom: 6px;
            }
            
            .streaming-text::after {
                content: ' ▍';
                color: var(--brand-red);
                animation: blink 0.8s infinite;
            }
            .streaming-text.done::after { content: ''; }
            @keyframes blink { 50% { opacity: 0; } }
        </style>
    </head>
    <body>

        <div class="top-navbar">
            <a class="logo-link" onclick="resetToHome()">
                <img class="brand-logo-img" src="/static/logo.jpg" alt="Huawei">
            </a>
        </div>

        <div class="container">
            <div class="brand-header">
                <h1>HUAWEI <span>CLOUD</span> MATCH</h1>
                <p class="subtitle">B2B Semantic Partnership Optimization Platform</p>
            </div>
            
            <div class="search-wrapper">
                <div class="search-box">
                    <input type="text" id="queryInput" placeholder="Specify project requirements to track partner alignment metrics..." autocomplete="off">
                    <button onclick="searchPartners()">Analyze</button>
                </div>
                
                <div id="suggestionsPanel" class="suggestions-panel">
                    <div class="suggestions-title">Trending Enterprise Requirements (Huawei Portfolio)</div>
                    <div class="suggestion-item" onclick="selectSuggestion('Deploy a Huawei Xinghe AI Campus Network to automate Wi-Fi 7 wireless optimization and safeguard business trade secrets.')">
                        <span class="suggestion-icon">→</span> Deploy Xinghe AI Campus Networks with Wi-Fi 7 security
                    </div>
                    <div class="suggestion-item" onclick="selectSuggestion('Build a high-performance AI Data Lake using OceanStor storage to train autonomous driving models and optimize big data pipelines.')">
                        <span class="suggestion-icon">→</span> Build OceanStor AI Data Lakes for autonomous driving pipelines
                    </div>
                    <div class="suggestion-item" onclick="selectSuggestion('Implement active-active hospital data centers and FTTO network solutions to build an intelligent medical pathology service.')">
                        <span class="suggestion-icon">→</span> Implement Active-Active Data Centers & FTTO for Healthcare
                    </div>
                    <div class="suggestion-item" onclick="selectSuggestion('Upgrade core digital finance architectures using open-source models and hybrid AI to transition toward Agentic Banking.')">
                        <span class="suggestion-icon">→</span> Upgrade financial systems via Hybrid AI and Agentic Banking
                    </div>
                    <div class="suggestion-item" onclick="selectSuggestion('Secure long-distance industrial assets using AI-powered optical fiber sensing and optical transmission for oil and gas pipelines.')">
                        <span class="suggestion-icon">→</span> Secure infrastructure using AI-powered Optical Fiber Sensing
                    </div>
                </div>
            </div>
            
            <div id="results" class="results-list"></div>
        </div>

        <div class="bottom-bg-graphic"></div>

        <script>
            const queryInput = document.getElementById('queryInput');
            const suggestionsPanel = document.getElementById('suggestionsPanel');
            const resultsContainer = document.getElementById('results');
            let eventSource = null;

            queryInput.addEventListener('focus', () => {
                suggestionsPanel.classList.add('visible');
            });

            document.addEventListener('click', (event) => {
                if (!event.target.closest('.search-wrapper')) {
                    suggestionsPanel.classList.remove('visible');
                }
            });

            function resetToHome() {
                if (eventSource) {
                    eventSource.close();
                }
                queryInput.value = "";
                resultsContainer.innerHTML = "";
                suggestionsPanel.classList.remove('visible');
            }

            function selectSuggestion(text) {
                queryInput.value = text;
                suggestionsPanel.classList.remove('visible');
                searchPartners();
            }

            function searchPartners() {
                const queryText = queryInput.value;
                if (!queryText.trim()) return;
                
                suggestionsPanel.classList.remove('visible');
                if (eventSource) eventSource.close();
                
                resultsContainer.innerHTML = `
                    <div style='text-align:center; padding: 40px 0;'>
                        <p style='color:var(--brand-red); font-weight:600; font-size:14px; text-transform:uppercase; letter-spacing:0.05em;'>Computing Semantic Proximity Vectors...</p>
                    </div>
                `;
                
                eventSource = new EventSource(`/stream-match?query=${encodeURIComponent(queryText)}`);
                
                eventSource.addEventListener('initial_matches', (event) => {
                    const data = JSON.parse(event.data);
                    resultsContainer.innerHTML = "";
                    
                    if (!data.matches || data.matches.length === 0) {
                        resultsContainer.innerHTML = `
                            <div style="text-align:center; padding: 40px 20px; border-radius:16px; border: 1px dashed var(--brand-red); background: rgba(230,0,18,0.02); margin-top: 10px;">
                                <p style="color:var(--brand-red); font-weight:700; font-size:15px; margin:0 0 4px 0; text-transform:uppercase;">No Verified Partners Aligned</p>
                                <p style="color:var(--text-muted); font-size:13px; margin:0;">The request did not pass the 50% semantic baseline matrix constraint rule.</p>
                            </div>
                        `;
                        eventSource.close();
                        return;
                    }
                    
                    data.matches.forEach((partner, index) => {
                        const matchScore = Math.round(partner.similarity * 100);
                        resultsContainer.innerHTML += `
                            <div class="card">
                                <div class="card-header">
                                    <div class="company-name">${partner.company_name}</div>
                                    <div class="badge">${matchScore}% ALIGNED</div>
                                </div>
                                <div class="industry">${partner.industry}</div>
                                <div class="objectives">${partner.objectives}</div>
                                
                                <div class="xai-justification">
                                    <div class="xai-title">Structural Alignment Analysis</div>
                                    <span id="ai-text-${index}" class="streaming-text">Analyzing architectural data vectors...</span>
                                </div>
                            </div>
                        `;
                    });
                });
                
                eventSource.addEventListener('ai_chunk', (event) => {
                    const data = JSON.parse(event.data);
                    const textTarget = document.getElementById(`ai-text-${data.partner_index}`);
                    if (textTarget) {
                        if (textTarget.innerText.includes("Analyzing architectural data vectors...")) {
                            textTarget.innerText = "“";
                        }
                        textTarget.innerText += data.text;
                    }
                });
                
                eventSource.addEventListener('done', () => {
                    document.querySelectorAll('.streaming-text').forEach(el => {
                        el.classList.add('done');
                        el.innerText += " ”";
                    });
                    eventSource.close();
                });
                
                eventSource.addEventListener('error', (err) => {
                    console.error("Pipeline breakdown:", err);
                    eventSource.close();
                });
            }
        </script>
    </body>
    </html>
    """
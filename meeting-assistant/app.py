import json
import re
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import ollama

app = FastAPI(title="AI Meeting Assistant API")

# Allow the page to call this API when it is opened through VS Code Live Server (port 5501)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5501", "http://localhost:5501"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Serve the UI from this same backend; only the static/ folder (images) is public,
# never the project root with the source code.
app.mount("/static", StaticFiles(directory="static"), name="static")

ollama_client = ollama.AsyncClient()


@app.get("/", response_class=FileResponse)
def home():
    return "index.html"

class MeetingPayload(BaseModel):
    transcript: str


# Structured extraction: the AI only pulls facts out of the transcript.
# Every number shown on the page is then computed in Python from these facts.
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "participants": {"type": "array", "items": {"type": "string"}},
        "decisions": {"type": "array", "items": {"type": "string"}},
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "owner": {"type": ["string", "null"]},
                    "deadline": {"type": ["string", "null"]},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["task", "owner", "deadline", "priority"],
            },
        },
        "risks": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "follow_up_email": {"type": "string"},
    },
    "required": ["summary", "participants", "decisions", "action_items", "risks", "open_questions", "follow_up_email"],
}

SPEAKER_LINE = re.compile(r"^\s*([A-Z][\w.\- ]{0,30}?)\s*:\s*(.+)$")
EMPTY_VALUES = ("", "null", "none", "not specified", "n/a", "unknown")


def _norm(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _in_transcript(value, transcript_norm):
    """True if the value literally appears in the transcript (blocks invented owners/deadlines)."""
    v = _norm(value)
    return v not in EMPTY_VALUES and v in transcript_norm


def _pct(part, total):
    return round(100 * part / total) if total else None


def compute_metrics(transcript, data):
    transcript_norm = _norm(transcript)
    words = len(re.findall(r"\w+", transcript))

    # Keep only participants, owners and deadlines that really appear in the transcript
    participants = []
    for name in data.get("participants", []):
        if _in_transcript(name, transcript_norm) and name.strip() not in participants:
            participants.append(name.strip())
    actions = []
    for item in data.get("action_items", []):
        owner, deadline = item.get("owner"), item.get("deadline")
        task = (item.get("task") or "").strip()
        if not task:
            continue
        task = task[0].upper() + task[1:]
        actions.append({
            "task": task,
            "owner": owner.strip() if _in_transcript(owner, transcript_norm) else None,
            "deadline": deadline.strip() if _in_transcript(deadline, transcript_norm) else None,
            "priority": item.get("priority") if item.get("priority") in ("high", "medium", "low") else "medium",
        })

    # Speaking share: words per speaker when the transcript uses "Name: text" lines,
    # otherwise how often each participant is mentioned in the notes
    spoken = {}
    for line in transcript.splitlines():
        m = SPEAKER_LINE.match(line)
        if m:
            name = m.group(1).strip()
            spoken[name] = spoken.get(name, 0) + len(re.findall(r"\w+", m.group(2)))
    if len(spoken) >= 2:
        share_basis = "words spoken"
        counts = spoken
    else:
        share_basis = "mentions in the notes"
        counts = {p: len(re.findall(r"\b" + re.escape(p.lower()) + r"\b", transcript_norm)) for p in participants}
        counts = {p: c for p, c in counts.items() if c}
    total_share = sum(counts.values())
    share = sorted(
        ({"name": n, "count": c, "percent": _pct(c, total_share)} for n, c in counts.items()),
        key=lambda x: -x["count"],
    )

    n_actions = len(actions)
    with_owner = sum(1 for a in actions if a["owner"])
    with_deadline = sum(1 for a in actions if a["deadline"])
    complete = sum(1 for a in actions if a["owner"] and a["deadline"])
    n_decisions = len(data.get("decisions", []))
    n_questions = len(data.get("open_questions", []))

    metrics = {
        "words": words,
        "participants": max(len(share), len(participants)),
        "action_items": n_actions,
        "with_owner": with_owner,
        "with_deadline": with_deadline,
        "owner_rate": _pct(with_owner, n_actions),
        "deadline_rate": _pct(with_deadline, n_actions),
        "accountability_rate": _pct(complete, n_actions),
        "decisions": n_decisions,
        "open_questions": n_questions,
        "resolution_rate": _pct(n_decisions, n_decisions + n_questions),
        "risks": len(data.get("risks", [])),
        "priorities": {p: sum(1 for a in actions if a["priority"] == p) for p in ("high", "medium", "low")},
        "share_basis": share_basis,
        "speaking_share": share,
    }
    return metrics, actions


def build_report(data, actions):
    """Plain-text report for the editable review box (copy/paste ready)."""
    def section(title, items):
        return ["", title] + ([f"- {i}" for i in items] or ["- None recorded"])

    lines = ["MEETING SUMMARY", (data.get("summary") or "").strip()]
    lines += section("DECISIONS", data.get("decisions", []))
    lines += section("ACTION ITEMS", [
        f"{a['task']} | Owner: {a['owner'] or 'Not specified'} | Deadline: {a['deadline'] or 'Not specified'} | Priority: {a['priority']}"
        for a in actions
    ])
    lines += section("RISKS / BLOCKERS", data.get("risks", []))
    lines += section("OPEN QUESTIONS", data.get("open_questions", []))
    lines += ["", "FOLLOW-UP EMAIL DRAFT", (data.get("follow_up_email") or "").strip()]
    return "\n".join(lines)


@app.post("/analyze-meeting")
async def analyze_meeting(payload: MeetingPayload):
    raw_text = payload.transcript
    print(f"\nReceived transcript processing request ({len(raw_text)} characters)...")

    prompt = f"""You are a corporate meeting analyst. Extract facts from the meeting transcript below.
Rules:
- Use ONLY information present in the transcript. Never invent names, dates, deadlines, numbers or tasks.
- owner: the exact name of the person responsible as written in the transcript, or null if nobody is named.
- deadline: the exact deadline wording from the transcript (e.g. "by Friday"), or null if none is mentioned.
- priority: high if the transcript signals urgency or a blocker, low if it is optional, otherwise medium.
- decisions: things the group agreed or decided. open_questions: points left unresolved.
- risks: blockers, delays or problems mentioned.
- summary: 2-3 sentences. follow_up_email: a short professional follow-up email.
Write everything in English.

TRANSCRIPT:
{raw_text}
"""

    try:
        response = await ollama_client.generate(
            model='llama3',
            prompt=prompt,
            format=EXTRACTION_SCHEMA,
            options={"temperature": 0},
        )
        data = json.loads(response.get('response', '') or '{}')
        metrics, actions = compute_metrics(raw_text, data)

        return {
            "success": True,
            "analysis": build_report(data, actions),
            "metrics": metrics,
            "action_items": actions,
        }

    except Exception as e:
        error_message = str(e)
        print(f"CRITICAL PIPELINE ERROR: {error_message}")
        return {
            "success": False,
            "analysis": "",
            "error": f"Backend processing failure: {error_message}"
        }


# Structure pour recevoir l'historique des messages du frontend
class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']  # the browser may not inject 'system' messages
    content: str

class ChatPayload(BaseModel):
    messages: list[ChatMessage]

@app.post("/chat-assistant")
async def chat_assistant(payload: ChatPayload):
    try:
        # Convertir le payload Pydantic en format de liste natif pour Ollama
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in payload.messages]
        
        # Injecter un "System Prompt" au début pour donner un rôle d'expert au bot
        # Nouveau System Prompt ultra-concis
        system_prompt = {
            "role": "system",
            "content": """You are an elite expert in Corporate Operations and Partnership Management.
Absolute rule: be concise (maximum 4-5 lines), direct, and adopt a modern, high-impact corporate tone.
Do NOT write any introduction or polite conclusion. Get straight to the point.
Use clear, professional terms (e.g. Strategic objectives, Alignment plan, Action plan).

LANGUAGE RULE (critical): Always reply in the SAME language as the user's most recent message.
If the user writes in English, reply entirely in English. If the user writes in French, reply entirely in French.
Never mix languages and never translate the user's language to another one."""
        }
        ollama_messages.insert(0, system_prompt)

        # Appel à Ollama en mode Chat
        response = await ollama_client.chat(
            model='llama3',
            messages=ollama_messages
        )
        
        return {
            "success": True,
            "reply": response['message']['content']
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
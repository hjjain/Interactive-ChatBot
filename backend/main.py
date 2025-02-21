from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from typing import List, Dict
import re

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OpenAI API key is missing. Set it in an environment variable.")

# Initialize OpenAI Client
client = OpenAI(api_key=api_key)

# Request models
class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str

SYSTEM_PROMPT = "You are an AI assistant providing helpful responses. Keep answers concise and relevant."

def filter_internal_dialogue(response: str) -> str:
    """Remove internal dialogue patterns from the response."""
    internal_patterns = [
        r"^(Alright|Ok|Okay|Well|So|Now|Let's see|I see|I understand|Let me|I should|I will|I can|The user|They said).*",
        r".*\b(the user|they said|they asked|they want|they're asking)\b.*",
        r".*\b(I need to|I'm going to|I'll try to|I should|Let me|I can)\b.*"
    ]
    for pattern in internal_patterns:
        if re.match(pattern, response, re.IGNORECASE):
            return "I'm sorry, but I couldn't generate a proper response."
    return response

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print("📩 User Message:", request.message)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if request.conversation_history:
            messages.extend(request.conversation_history)
        messages.append({"role": "user", "content": request.message})

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150,
            presence_penalty=0.6,
            frequency_penalty=0.4,
        )
        reply = response.choices[0].message.content
        filtered_reply = filter_internal_dialogue(reply)
        conversation_id = str(hash(str(messages)))[-8:]

        return ChatResponse(reply=filtered_reply, conversation_id=conversation_id)
    
    except Exception as e:
        print("🚨 Error:", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": f"🚨 Chatbot Error: {str(e)}", "type": type(e).__name__}
        )

# Run server: uvicorn main:app --reload

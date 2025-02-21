from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Optional
import json
import io

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

class ChatResponse(BaseModel):
    reply: str
    conversation_id: str

import base64


import base64
from fastapi import UploadFile

async def extract_text_from_image(image: UploadFile) -> str:
    """Extract text from an image using OpenAI's GPT-4 Turbo Vision model."""
    try:
        # Read image bytes
        image_bytes = await image.read()

        # Convert image bytes to Base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # OpenAI API request using GPT-4 Turbo
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that extracts text from images."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Extract the text from this image:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ],
            max_tokens=300
        )

        # Ensure response has valid content
        extracted_text = response.choices[0].message.content if response.choices else "No text extracted."
        
        if not isinstance(extracted_text, str):
            extracted_text = str(extracted_text)  # Ensure it's a string

        return extracted_text.strip()

    except Exception as e:
        print(f"🚨 Error extracting text from image: {str(e)}")
        return "Error processing image."


async def analyze_image_text(extracted_text: str, user_query: str) -> str:
    """Analyze extracted text based on user query using GPT-4."""
    try:
        if extracted_text:
            prompt = f"""I've extracted the following text from an image:
            ---
            {extracted_text}
            ---
            User's question: {user_query}
            Please analyze this text and answer the user's question. If the question isn't directly about the text, 
            incorporate the text content into your response where relevant."""
        else:
            prompt = f"""No text could be clearly extracted from the image. 
            The user asked: {user_query}
            Please provide a response acknowledging that text extraction was unsuccessful and offer alternative suggestions."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant analyzing text extracted from images. Provide clear, accurate responses about the text content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"🚨 Error in GPT analysis: {str(e)}")
        return "I encountered an error analyzing the image text. Please try again."

@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    image: Optional[UploadFile] = File(None),
    conversation_history: str = Form(...)
):
    try:
        if image:
            extracted_text = await extract_text_from_image(image)
            reply = await analyze_image_text(extracted_text, message)
        else:
            history = json.loads(conversation_history)
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                *[{"role": m["role"], "content": m["content"]} for m in history if "content" in m],
                {"role": "user", "content": message}
            ]

            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            reply = response.choices[0].message.content

        conversation_id = str(hash(message))[-8:]
        return ChatResponse(reply=reply, conversation_id=conversation_id)

    except Exception as e:
        print("🚨 Error:", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": f"🚨 Chatbot Error: {str(e)}", "type": type(e).__name__}
        )


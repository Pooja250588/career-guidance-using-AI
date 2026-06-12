from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
from PIL import Image
import pytesseract
from io import BytesIO
import fitz

load_dotenv()
print("OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("OPENAI_API_KEY")

client = None
if api_key and api_key != "sk-your-api-key-here":
    client = OpenAI(api_key=api_key)
conversation_history: List[Dict] = []

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    is_context_setting: bool = False
    chat_mode: bool = False

frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

app.mount("/static", StaticFiles(directory=frontend_path), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

@app.get("/{path:path}")
def serve_static_files(path: str):
    file_path = os.path.join(frontend_path, path)

    if path.endswith(".html") and os.path.exists(file_path):
        return FileResponse(file_path)

    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.post("/api/chat")
def chat(request: ChatRequest):
    return {
        "response": f"Demo Mode: You asked '{request.message}'. AI API is not configured."
    }
        
        

@app.post("/api/reset")
def reset_conversation():
    global conversation_history
    conversation_history = []
    return {"status": "Conversation reset successfully"}

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded-images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    try:
        file_data = await file.read()

        if file.content_type == "application/pdf":
            pdf_document = fitz.open(stream=file_data, filetype="pdf")
            text = "".join(page.get_text() for page in pdf_document)

            pdf_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(pdf_path, "wb") as f:
                f.write(file_data)

            return {"extracted_text": text, "saved_file_path": pdf_path}

        image = Image.open(BytesIO(file_data))

        image_path = os.path.join(UPLOAD_DIR, file.filename)
        image.save(image_path)

        text = pytesseract.image_to_string(image)

        return {"extracted_text": text, "saved_image_path": image_path}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

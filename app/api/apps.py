from fastapi import APIRouter, HTTPException
from models.ChatModel import ClientChatInputModel

from google import genai
from google.genai.types import HttpOptions

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

@router.post("/apps/chat/", tags=["apps"])
def app_chat_function(user_input: ClientChatInputModel):
  '''
  We need the text from the user - for now we do this
  We need possible documents or links
  '''
  
  client = genai.Client(
    http_options=HttpOptions(api_version="v1"),
    project=PROJECT_ID,
    location=CLOUD_LOCATION,
  )

  chat = client.chats.create(
    model="gemini-3.5-flash-lite",
  )

  response = chat.send_message(
    message=f"{user_input}"
  )

  
  print(response.text)

  return {
    "message": response.text 
  }

  
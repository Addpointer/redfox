from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from openai import OpenAI
from routers import apps


load_dotenv()

origins = [
  "http://localhost:3000",
]

QWEN_API_KEY = os.getenv("QWEN_API_KEY")

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(apps.router)


@app.get("/")
def server_root():
  return {
    "message": "Hello to aiserver"
  }

@app.get("/aitest")
def server_ai_test():
  client = OpenAI(
    api_key=QWEN_API_KEY,
    base_url='https://dashscope-intl.aliyuncs.com/compatible-mode/v1'
  )

  completion = client.chat.completions.create(
    model="qwen3.6-flash",
    messages=[
      {"role": "user", "content": "Hello! Tell me a fun fact about AI."}
    ]
  )

  chat_response = completion.choices[0].message.content
  
  print(completion.choices[0].message.content)

  return {
    "message": chat_response 
  }


# def main():
#   print("Hello from aiserver!")


# if __name__ == "__main__":
#   main()

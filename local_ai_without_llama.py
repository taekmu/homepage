from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from llama_cpp import Llama

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# 모델 로드 (RAM 적을 때 설정)
llm = Llama(
    model_path="D:/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_gpu_layers=0
)

class Prompt(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index_local_ai.html", {"request": request})


@app.post("/chat")
async def chat(prompt: Prompt):

    output = llm(
        f"### User:\n{prompt.message}\n### Assistant:\n",
        max_tokens=200,
        stop=["### User:"]
    )

    text = output["choices"][0]["text"]

    return {"response": text}
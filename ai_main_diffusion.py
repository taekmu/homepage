from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from diffusers import StableDiffusionPipeline
import torch, base64
from io import BytesIO

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# -----------------------------
# 모델 로드 (CPU + 메모리 최적화)
# -----------------------------
model_path = "D:/models/v1-5-pruned-emaonly-fp16.safetensors"

pipe = StableDiffusionPipeline.from_single_file(
    model_path,
    torch_dtype=torch.float32,
    load_safety_checker=False  # 메모리 절약을 위해 필수
)

pipe.to("cpu")
pipe.enable_attention_slicing()  # CPU 메모리 절약

# -----------------------------
# HTML UI
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index_ai_diffusion.html", {"request": request})

# -----------------------------
# 이미지 생성
# -----------------------------
@app.post("/generate")
async def generate(request: Request, prompt: str = Form(...)):
    image = pipe(prompt, guidance_scale=7.5, num_inference_steps=15).images[0]
   
    # 이미지 → base64
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return templates.TemplateResponse("index_ai_diffusion.html", {
        "request": request,
        "prompt": prompt,
        "img_data": img_str
    })
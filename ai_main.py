from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
from pydantic import BaseModel
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

# Ollama 로컬 서버 주소
OLLAMA_API = "http://localhost:11434/api"

class ChatRequest(BaseModel):
    model: str
    prompt: str

@app.get("/")
async def read_index():
    return FileResponse('ai_index.html')

@app.get("/models")
async def get_models():
    """로컬 Ollama에 설치된 모델 리스트 반환"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_API}/tags")
            # 모델 이름들만 추출
            models = [m['name'] for m in response.json().get('models', [])]
            return {"models": models}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Ollama 서버가 꺼져있습니다.")

@app.post("/chat")
async def chat(req: ChatRequest):
    # 1. Ollama 주소 확인 (기본 11434 포트)
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": req.model, 
        "prompt": req.prompt, 
        "stream": False
    }
    # 1. 측정 시작 시간 기록
    start_time = time.perf_counter()

    # 2. 타임아웃을 넉넉하게(None 또는 120초) 설정
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            logger.info(f"AI 요청 시작: 모델={req.model}, 프롬프트={req.prompt}")
            
            response = await client.post(url, json=payload)
            
            # 응답 코드가 200이 아니면 에러 발생시킴
            response.raise_for_status()
            # 2. 측정 종료 시간 기록 및 계산
            end_time = time.perf_counter()
            duration = round(end_time - start_time, 2) # 소수점 둘째자리까지
                       
            result = response.json()
            # 터미널 로그에 실행 시간 출력
            logger.info(f"AI 응답 완료 - 소요 시간: {duration}초")           
            
            return {"response": result.get("response"), "duration": duration}
        

        except httpx.ConnectError:
            logger.error("Ollama 서버에 연결할 수 없습니다. 'ollama serve' 확인!")
            raise HTTPException(status_code=503, detail="Ollama 서버 미가동")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama 서버 에러 응답: {e.response.text}")
            raise HTTPException(status_code=500, detail="AI 모델 실행 오류")
        except Exception as e:
            logger.error(f"예상치 못한 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
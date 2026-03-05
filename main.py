import asyncio
import random
import httpx
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 전역 클라이언트 하나만 유지 (성능 이점)
client = httpx.AsyncClient(timeout=10)
connections = set()
current_data = []

def calculate_probability(price, change_rate):
    # 수식 최적화: 불필요한 형변환 감소
    base_prob = 50 + (change_rate * 0.5)
    price_factor = (int(price) % 100) / 10
    noise = random.uniform(-10, 10)
    return round(max(35, min(95, base_prob + price_factor + noise)), 1)

async def get_bithumb_data():
    try:
        url = "https://api.bithumb.com/public/ticker/ALL_KRW"
        res = await client.get(url)
        data = res.json()

        if data.get("status") != "0000":
            return None

        all_data = data["data"]
        all_data.pop("date", None)

        # 정렬 및 슬라이싱 최적화
        sorted_items = sorted(
            all_data.items(),
            key=lambda x: float(x[1].get("acc_trade_value_24H", 0)),
            reverse=True
        )[:10]

        now = datetime.now().strftime("%H:%M:%S")
        return [
            {
                "ticker": ticker,
                "price": float(info["closing_price"]),
                "change_rate": float(info["fluctate_rate_24H"]),
                "value_24h": float(info["acc_trade_value_24H"]),
                "probability": calculate_probability(float(info["closing_price"]), float(info["fluctate_rate_24H"])),
                "timestamp": now
            }
            for ticker, info in sorted_items
        ]
    except Exception as e:
        print(f"API ERROR: {e}")
        return None

async def data_loop():
    global current_data
    while True:
        try:
            # 접속자가 있을 때만 API 호출 (CPU/네트워크 절약 핵심)
            if connections:
                data = await get_bithumb_data()
                if data:
                    current_data = data
                    # 리스트 복사본으로 순회하여 런타임 에러 방지
                    tasks = [ws.send_json(current_data) for ws in list(connections)]
                    if tasks:
                        # 여러 전송 작업을 병렬 처리
                        await asyncio.gather(*tasks, return_exceptions=True)
            
            # 접속자가 없으면 5초, 있으면 3초 대기 (유동적 조절 가능)
            await asyncio.sleep(3 if connections else 5)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup():
    # 백그라운드 태스크를 변수에 저장하여 참조 유지
    app.state.broadcast_task = asyncio.create_task(data_loop())

@app.on_event("shutdown")
async def shutdown():
    app.state.broadcast_task.cancel()
    await client.aclose()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("real.html", {"request": request})

@app.websocket("/ws/stats")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    try:
        if current_data:
            await ws.send_json(current_data)
        
        # 클라이언트의 연결 끊김을 즉시 감지하는 루프
        while True:
            await ws.receive_text() # 클라이언트가 보낸 메시지 대기 (연결 확인용)
    except WebSocketDisconnect:
        pass
    finally:
        connections.discard(ws)
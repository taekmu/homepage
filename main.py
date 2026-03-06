import asyncio
import random
import httpx
import msgspec  # pip install msgspec (JSON보다 10배 빠름)
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# 데이터 구조 정의 (msgspec Struct 사용으로 메모리 및 속도 최적화)
class TickerInfo(msgspec.Struct):
    ticker: str
    price: float
    change_rate: float
    value_24h: float
    probability: float
    timestamp: str

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = httpx.AsyncClient(timeout=10)
connections = set()
# 미리 인코딩된 바이너리 데이터를 저장 (중복 인코딩 방지 핵심)
cached_binary_data = b""

def calculate_probability(price: float, change_rate: float) -> float:
    base_prob = 50 + (change_rate * 0.5)
    price_factor = (int(price) % 100) / 10
    noise = random.uniform(-10, 10)
    return round(max(35, min(95, base_prob + price_factor + noise)), 1)

async def get_bithumb_data():
    try:
        url = "https://api.bithumb.com/public/ticker/ALL_KRW"
        res = await client.get(url)
        raw_res = res.json()

        if raw_res.get("status") != "0000":
            return None

        all_data = raw_res["data"]
        all_data.pop("date", None)

        # 상위 10개 추출 및 가공
        sorted_items = sorted(
            all_data.items(),
            key=lambda x: float(x[1].get("acc_trade_value_24H", 0)),
            reverse=True
        )[:10]

        now = datetime.now().strftime("%H:%M:%S")
        
        return [
            TickerInfo(
                ticker=ticker,
                price=float(info["closing_price"]),
                change_rate=float(info["fluctate_rate_24H"]),
                value_24h=float(info["acc_trade_value_24H"]),
                probability=calculate_probability(float(info["closing_price"]), float(info["fluctate_rate_24H"])),
                timestamp=now
            )
            for ticker, info in sorted_items
        ]
    except Exception as e:
        print(f"API Error: {e}")
        return None

async def data_loop():
    global cached_binary_data
    while True:
        try:
            if connections:
                data_list = await get_bithumb_data()
                if data_list:
                    # [개선 핵심] 데이터를 딱 한 번만 바이너리 JSON으로 변환
                    cached_binary_data = msgspec.json.encode(data_list)
                    
                    # 모든 소켓에 직렬화 과정 없이 그대로 전송 (CPU 점유율 급감)
                    if connections:
                        await asyncio.gather(
                            *(ws.send_bytes(cached_binary_data) for ws in connections),
                            return_exceptions=True
                        )
            
            # 빗썸 API 부하 및 UI 렌더링 최적화를 위해 1초 정도로 조절 가능
            await asyncio.sleep(1) 
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup():
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
        # 접속 즉시 기존 데이터가 있다면 전송
        if cached_binary_data:
            await ws.send_bytes(cached_binary_data)
        
        while True:
            # 클라이언트 연결 유지 확인 (Pong 대기)
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connections.discard(ws)
import asyncio
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from fastapi.staticfiles import StaticFiles
import httpx
import random

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = httpx.AsyncClient()

# 전역 데이터 저장소
current_data = []

# -----------------------------
# 확률 계산
# -----------------------------
def calculate_probability(price, change_rate):
    base_prob = 50 + (change_rate * 0.5)
    price_factor = (int(price) % 100) / 10
    noise = random.uniform(-10, 10)

    final_prob = base_prob + price_factor + noise
    return round(max(35, min(95, final_prob)), 1)

# -----------------------------
# 빗썸 데이터 가져오기
# -----------------------------
async def get_bithumb_top_value():
    try:
        url = "https://api.bithumb.com/public/ticker/ALL_KRW"
        res = await client.get(url)
        res = res.json()

        if res["status"] == "0000":

            all_data = res["data"]

            if "date" in all_data:
                del all_data["date"]

            sorted_items = sorted(
                all_data.items(),
                key=lambda x: float(x[1].get("acc_trade_value_24H", 0)),
                reverse=True
            )[:10]

            top10 = []

            for ticker, info in sorted_items:

                price = float(info["closing_price"])
                change_rate = float(info["fluctate_rate_24H"])

                top10.append({
                    "ticker": ticker,
                    "price": price,
                    "change_rate": change_rate,
                    "value_24h": float(info["acc_trade_value_24H"]),
                    "probability": calculate_probability(price, change_rate),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

            return top10

    except Exception as e:
        print("Server Error:", e)

    return []

# -----------------------------
# 백그라운드 루프 (핵심)
# -----------------------------
async def data_fetch_loop():
    global current_data

    while True:
        data = await get_bithumb_top_value()

        if data:
            current_data = data

        await asyncio.sleep(2)

# -----------------------------
# 서버 시작 시 실행
# -----------------------------
@app.on_event("startup")
async def startup_event():

    asyncio.create_task(data_fetch_loop())

# -----------------------------
# HTML
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("real.html", {"request": request})

# -----------------------------
# WebSocket
# -----------------------------
@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    try:
        while True:

            if current_data:
                await websocket.send_json(current_data)

            await asyncio.sleep(1)

    except:
        pass

# -----------------------------
# 종료 시 httpx 종료
# -----------------------------
@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
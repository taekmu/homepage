import asyncio
import random
import httpx

from datetime import datetime
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = httpx.AsyncClient()

# 전역 데이터
current_data = []

# 연결된 websocket 목록
connections = set()


# -----------------------------
# probability 계산
# -----------------------------
def calculate_probability(price, change_rate):

    base_prob = 50 + (change_rate * 0.5)
    price_factor = (int(price) % 100) / 10
    noise = random.uniform(-10, 10)

    final_prob = base_prob + price_factor + noise

    return round(max(35, min(95, final_prob)), 1)


# -----------------------------
# 빗썸 API
# -----------------------------
async def get_bithumb_top_value():

    try:

        url = "https://api.bithumb.com/public/ticker/ALL_KRW"

        res = await client.get(url)
        res = res.json()

        if res["status"] != "0000":
            return None

        all_data = res["data"]
        all_data.pop("date", None)

        sorted_items = sorted(
            all_data.items(),
            key=lambda x: float(x[1].get("acc_trade_value_24H", 0)),
            reverse=True
        )[:10]

        result = []

        now = datetime.now().strftime("%H:%M:%S")

        for ticker, info in sorted_items:

            price = float(info["closing_price"])
            change_rate = float(info["fluctate_rate_24H"])

            result.append({
                "ticker": ticker,
                "price": price,
                "change_rate": change_rate,
                "value_24h": float(info["acc_trade_value_24H"]),
                "probability": calculate_probability(price, change_rate),
                "timestamp": now
            })

        return result

    except Exception as e:

        print("API ERROR:", e)
        return None


# -----------------------------
# 데이터 수집 루프 (1개만 실행)
# -----------------------------
async def data_loop():

    global current_data

    while True:

        data = await get_bithumb_top_value()

        if data:

            current_data = data

            dead = []

            for ws in connections:

                try:
                    await ws.send_json(current_data)
                except:
                    dead.append(ws)

            for ws in dead:
                connections.discard(ws)

        await asyncio.sleep(2)


# -----------------------------
# 서버 시작
# -----------------------------
@app.on_event("startup")
async def startup():

    asyncio.create_task(data_loop())


# -----------------------------
# 서버 종료
# -----------------------------
@app.on_event("shutdown")
async def shutdown():

    await client.aclose()


# -----------------------------
# HTML
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse("real.html", {"request": request})


# -----------------------------
# WebSocket
# -----------------------------
@app.websocket("/ws/stats")
async def websocket_endpoint(ws: WebSocket):

    await ws.accept()

    connections.add(ws)

    try:

        # 최초 데이터 바로 전송
        if current_data:
            await ws.send_json(current_data)

        while True:
            await asyncio.sleep(3600)

    except:
        pass

    finally:
        connections.discard(ws)
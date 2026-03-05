import asyncio
import requests
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from fastapi.staticfiles import StaticFiles # 추가


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# real_main.py 내 데이터 가공 부분에 추가
def calculate_probability(price, change_rate):
    # 실제로는 과거 차트 데이터를 분석해야 하지만, 
    # 여기서는 실시간 지표인 변동률과 랜덤 노이즈를 섞어 '예측 점수'를 시뮬레이션합니다.
    # 과매도 상태(하락폭이 큼)에서 반등할 확률이나 추세 추종 로직을 적용할 수 있습니다.
    
    import random
    base_prob = 50 + (change_rate * 0.5) # 변동폭이 클수록 추세 지속/반등 확률 반영 ->0.5로 하향조정
    # 현재 가격의 끝자리를 활용해 심리적 지지/저항 '척도'를 시뮬레이션 (더 역동적임)
    price_factor = (int(price) % 100) / 10
    # 40% ~ 85% 사이에서 더 많이 흔들리도록 노이즈 강화
    noise = random.uniform(-10, 10)
    final_prob = base_prob + price_factor + noise
    return round(max(35, min(95, final_prob)), 1)
    
def get_bithumb_top_value():
    try:
        # 모든 코인 정보 가져오기
        url = "https://api.bithumb.com/public/ticker/ALL_KRW"
        res = requests.get(url).json()
        
        if res['status'] == '0000':
            all_data = res['data']
            if 'date' in all_data: del all_data['date']
            
            # [핵심 수정] 거래금액(acc_trade_value_24H) 기준 내림차순 정렬
            # 빗썸 API에서 acc_trade_value_24H는 최근 24시간 누적 거래액(KRW)입니다.
            sorted_items = sorted(
                all_data.items(), 
                key=lambda x: float(x[1].get('acc_trade_value_24H', 0)), 
                reverse=True
            )[:10]
            
            top10 = []
            for ticker, info in sorted_items:
                top10.append({
                    "ticker": ticker,
                    "price": float(info['closing_price']),
                    "change_rate": float(info['fluctate_rate_24H']),
                    "value_24h": float(info['acc_trade_value_24H']), # 거래금액 추가
                    "probability": calculate_probability(float(info['closing_price']), float(info['fluctate_rate_24H'])),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
            return top10
    except Exception as e:
        print(f"Server Error: {e}")
        return []

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("real.html", {"request": request})

@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = get_bithumb_top_value()
            if data:
                await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except:
        pass
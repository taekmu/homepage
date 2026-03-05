import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

# static 폴더가 없으면 에러가 나므로 확인용 코드 추가
if not os.path.exists("static"):
    os.makedirs("static")

# static 폴더 연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# 현재 서버의 메모리에 위치 저장 (초기값: 천안역)
current_pos = {"lat": 36.8151, "lng": 127.1478}

@app.get("/")
async def get():
    # 경로가 정확한지 확인하며 HTML 반환
    file_path = "static/map.html"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>static/map.html 파일을 찾을 수 없습니다.</h1>")

@app.websocket("/ws/map")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 브라우저로부터 목적지 데이터 수신
            data = await websocket.receive_json()
            dest_lat = data.get("lat")
            dest_lng = data.get("lng")
            place_name = data.get("name", "목적지")

            # 출발지 설정
            start_lat, start_lng = current_pos["lat"], current_pos["lng"]
            
            # 30단계로 나누어 부드럽게 이동
            steps = 30
            for i in range(1, steps + 1):
                inter_lat = start_lat + (dest_lat - start_lat) * (i / steps)
                inter_lng = start_lng + (dest_lng - start_lng) * (i / steps)
                
                # 전역 변수 업데이트 (다음 이동의 출발점이 됨)
                current_pos["lat"], current_pos["lng"] = inter_lat, inter_lng
                
                await websocket.send_json({
                    "lat": inter_lat, 
                    "lng": inter_lng,
                    "name": place_name
                })
                await asyncio.sleep(0.05) # 이동 속도 조절
                
    except Exception as e:
        print(f"WebSocket 연결 종료: {e}")
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# 템플릿 디렉터리 지정
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # 텍스트 파일을 열어서 라인 단위로 읽기d
    with open("users.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    f.close()

    # 첫 줄은 헤더이므로 데이터 부분만 리스트로 만들기
    data_rows = []
    for i, line in enumerate(lines):
        if i == 0:  # 헤더는 스킵
            continue
        parts = line.split(",")  # 콤마로 분리
        row = {
            "no": parts[0],
            "user_id": parts[1],
            "user_name": parts[2]
        }
        data_rows.append(row)
    print(data_rows)

    # HTML 템플릿에 리스트 데이터 넘기기
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "rows": data_rows}
    )
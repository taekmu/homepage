from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 텍스트 파일을 읽어서 리스트로 반환
def read_data():
    with open("users.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    rows = []
    for i, line in enumerate(lines):
        if i == 0:  # 헤더는 제외
            continue
        no, user_id, user_name = line.split(",")
        rows.append({"no": no, "user_id": user_id, "user_name": user_name})
    return rows

# 텍스트 파일에 리스트를 저장
def save_data(rows):
    with open("users.txt", "w", encoding="utf-8") as f:
        f.write("no,user_id,user_name\n")
        for r in rows:
            f.write(f"{r['no']},{r['user_id']},{r['user_name']}\n")

@app.get("/", response_class=HTMLResponse)
async def show_list(request: Request):
    rows = read_data()
    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})

@app.post("/add")
async def add_user(
    request: Request,
    user_id: str = Form(...),
    user_name: str = Form(...)
):
    rows = read_data()
    # 번호 자동 증가
    new_no = str(max([int(r["no"]) for r in rows] + [0]) + 1)
    rows.append({"no": new_no, "user_id": user_id, "user_name": user_name})
    save_data(rows)
    return RedirectResponse("/", status_code=303)

@app.post("/delete")
async def delete_user(no: str = Form(...)):
    rows = read_data()
    rows = [r for r in rows if r["no"] != no]
    save_data(rows)
    return RedirectResponse("/", status_code=303)

@app.post("/update")
async def update_user(
    no: str = Form(...),
    user_id: str = Form(...),
    user_name: str = Form(...)
):
    rows = read_data()
    for r in rows:
        if r["no"] == no:
            r["user_id"] = user_id
            r["user_name"] = user_name
            break
    save_data(rows)
    return RedirectResponse("/", status_code=303)
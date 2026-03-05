async def app(scope, receive, send):
    # HTTP 요청이 아니면 무시
    if scope["type"] != "http":
        return

    method = scope["method"]
    path = scope["path"]

    # GET /api 요청인 경우
    if method == "GET" and path == "/api":
        # 쿼리 스트링 받아오기
        query_bytes = scope.get("query_string", b"")
        query_str = query_bytes.decode("utf-8")  # b"name=Alice" → "name=Alice"

        # 기본값
        name = ""

        # 단순 파싱: name=값 형태
        if query_str.startswith("name="):
            name = query_str.split("=", 1)[1]

        # HTML 응답 생성
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Result</title></head>
        <body>
            <h1>안녕하세요, {name}님!</h1>
            <p>서버로부터 받은 값이 여기에 반영되었습니다.</p>
        </body>
        </html>
        """.encode("utf-8")

        # 응답 헤더 + body 보내기
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8")
            ],
        })
        await send({
            "type": "http.response.body",
            "body": html_content,
        })
    else:
        # 기본 페이지 또는 404
        default_html = b"""
        <html>
        <body>
            <h2>Welcome!</h2>
            <p>Use /api?name=YourName to see dynamic output.</p>
        </body>
        </html>
        """
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8")
            ],
        })
        await send({
            "type": "http.response.body",
            "body": default_html,
        })
from locust import HttpUser, task, between

class FastAPIUser(HttpUser):
    # 각 사용자가 요청 사이에 1~2초간 대기 (실제 사용자 행동 모사)
    wait_time = between(1, 2)

    @task
    def get_user(self):
        # DB 조회가 일어나는 엔드포인트를 집중적으로 테스트
        self.client.get("/users/1")
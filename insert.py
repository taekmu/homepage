import asyncio
from database import engine, async_session_factory
from models import Base, User

async def init_db():
    # 1. 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. id=1인 테스트 데이터 넣기
    async with async_session_factory() as session:
        # 데이터가 이미 있는지 확인 후 없으면 추가
        test_user = User(username="performance_tester", email="test@example.com")
        session.add(test_user)
        await session.commit()
    print("\n✨ [성공] 테이블 생성 및 테스트 유저(id=1) 등록 완료!")

asyncio.run(init_db())
exit()
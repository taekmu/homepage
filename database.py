# AsyncSessionmaker 를 async_sessionmaker 로 변경 (전부 소문자)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

# 1. 비동기 DB URL 설정 (asyncpg 드라이버 사용)
DATABASE_URL = "postgresql+asyncpg://postgres:패스워드@localhost:5432/postgres"

# 2. 엔진 생성 (커넥션 풀 설정 포함)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # SQL 로그 출력 여부
    pool_size=50, # 최대 커넥션 수    
    max_overflow=50, # 최대 커넥션 수 초과 시 추가로 생성할 수 있는 커넥션 수
    # 3. 연결을 얻기 위해 기다리는 최대 시간 (초)
    pool_timeout=60,# 커넥션 풀에서 커넥션을 얻기 위해 기다리는 최대 시간 (초)
    pool_recycle=3600, # 1시간마다 연결 갱신
)
# 3. 세션 팩토리 생성
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 커밋 후 객체 증발 방지
)
# 4. 베이스 클래스 (모델용)
class Base(DeclarativeBase):
    pass
# 5. Dependency Injection용 세션 생성기
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()  # 예외 없으면 자동 커밋
        except Exception:
            await session.rollback() # 에러 발생 시 롤백
            raise
        finally:
            await session.close()    # 세션 반드시 반환

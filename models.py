from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base  # database.py에서 만든 Base를 가져옵니다.

class User(Base):
    __tablename__ = "users"

    # Mapped와 mapped_column은 SQLAlchemy 2.0의 최신 타이핑 방식입니다.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    # 추가 예시: 상태값 등
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<User(username={self.username!r}, email={self.email!r})>"
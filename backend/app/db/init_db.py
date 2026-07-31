from app.db.base import Base
from app.db.session import engine
from app.models.document import Document  # noqa: F401
from app.models.ingestion_job import IngestionJob  # noqa: F401
from app.models.book_curation import BookCuration  # noqa: F401

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    init_db()
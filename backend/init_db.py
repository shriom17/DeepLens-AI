from backend.database import engine, Base
from backend.models import User, Notice


Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
from fastapi import FastAPI
from app.database import engine, Base, run_light_migrations
from app.routes import chat

# Create database tables
# Create tables & migrate

run_light_migrations()  # <-- add
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chatbot Backend with PostgreSQL")

# root
@app.get("/")
def read_root():
    return {"message": "Welcome to the Chatbot API"}

# Routes
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

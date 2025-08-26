from fastapi import FastAPI
from app.database import engine, Base
from app.routes import chat

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chatbot Backend with PostgreSQL")

# root
@app.get("/")
def read_root():
    return {"message": "Welcome to the Chatbot API"}

# Routes
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

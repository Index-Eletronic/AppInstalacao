import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB = os.getenv("MONGO_DB", "app_instalacao")

if not MONGO_URL:
    raise RuntimeError("A variável MONGO_URL não foi configurada.")

client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000
)

db = client[MONGO_DB]
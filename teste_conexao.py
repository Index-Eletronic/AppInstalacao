import asyncio
from app.database import client

async def main():
    resposta = await client.admin.command("ping")
    print(resposta)

asyncio.run(main())
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.api import auth, pet, inventory, settings as settings_api

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QQ Pet Server",
    description="QQ 宠物服务器端 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(pet.router, prefix="/api/pet", tags=["宠物数据"])
app.include_router(inventory.router, prefix="/api/pet/inventory", tags=["背包"])
app.include_router(settings_api.router, prefix="/api/pet/settings", tags=["设置"])


@app.get("/")
def root():
    return {"message": "QQ Pet Server", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True
    )

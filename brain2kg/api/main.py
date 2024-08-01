import logging

from fastapi import FastAPI

from brain2kg.api.routers.eda import router as eda_router

app = FastAPI()
logger = logging.getLogger(__name__)
app.include_router(eda_router)
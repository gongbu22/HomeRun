import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Depends, Query, Form, UploadFile, File
from sqlalchemy.orm import Session

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.dbfactory import db_startup, db_shutdown, get_db
from app.model.rental import Rental
from app.routes.club import club_router
from app.routes.management import management_router
from app.routes.mypage import mypage_router
from app.routes.notification import notification_router
from app.routes.payment import payment_router
from app.routes.rental import rental_router
from app.routes.reservation import reservation_router
from app.routes.reservation_api import reservation_api_router
from app.routes.user import user_router
from app.service.rental import RentalService, process_upload

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Lifespan 관리 함수 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_startup()  # 서버 시작 시 실행될 코드
    yield
    await db_shutdown()  # 서버 종료 시 실행될 코드

# FastAPI 앱 인스턴스 생성 시 lifespan 함수 전달
app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory='views/templates')
app.mount('/static', StaticFiles(directory='views/static'), name='static')
# Static files 설정
app.mount("/cdn/img", StaticFiles(directory="C:/java/nginx-1.26.2/html/cdn/img"), name="cdn")

app.include_router(club_router, prefix='/club')
app.include_router(management_router, prefix='/management')
app.include_router(mypage_router, prefix='/mypage')
app.include_router(notification_router, prefix='/notification')
app.include_router(payment_router, prefix='/payment')
app.include_router(rental_router, prefix='/rental')
app.include_router(reservation_api_router, prefix="/api")
app.include_router(reservation_router, prefix="/reservation")
app.include_router(user_router, prefix='/user')


@app.get("/", response_class=HTMLResponse)
async def index(req: Request):
    return templates.TemplateResponse('index.html', {'request': req})


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/rental/add")
async def add_rental(
        title: str = Form(...),
        contents: str = Form(...),
        people: int = Form(...),
        price: int = Form(...),
        address: str = Form(...),
        latitude: float = Form(...),
        longitude: float = Form(...),
        sportsno: int = Form(...),
        sigunguno: int = Form(...),
        available_dates: str = Form(...),  # 문자열로 들어오는 available_dates 추가
        files: List[UploadFile] = File([]),  # 파일 업로드를 위한 설정
        db: Session = Depends(get_db)
):
    attachs = await process_upload(files)
    rental_data = {
        "title": title,
        "contents": contents,
        "people": people,
        "price": price,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "sportsno": sportsno,
        "sigunguno": sigunguno,
    }

    try:
        RentalService.insert_rental(rental_data, attachs, db)
        return {"status": "success", "message": "Rental added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', reload=True)
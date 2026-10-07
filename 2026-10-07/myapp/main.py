from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/sub.html")
def sub(request: Request):

    products = [
        {"name": "사과", "price": 1000},
        {"name": "바나나", "price": 2000},
        {"name": "딸기", "price": 3000}
    ]

    return templates.TemplateResponse(
        request=request,
        name="sub.html",
        context={"products": products}
    )
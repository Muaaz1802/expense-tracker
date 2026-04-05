from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.routers.auth import router as auth_router
from app.routers.budgets import router as budgets_router
from app.routers.categories import router as categories_router
from app.routers.expenses import router as expenses_router
from app.routers.reports import router as reports_router

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"errors": exc.errors()},
    )


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request, "message": "Expense Tracker API is running"},
        request=request,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(expenses_router, prefix="/api/v1/expenses")
app.include_router(categories_router, prefix="/api/v1/categories")
app.include_router(budgets_router, prefix="/api/v1/budgets")
app.include_router(reports_router, prefix="/api/v1/reports")

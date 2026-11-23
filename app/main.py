from fastapi import FastAPI, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from app.routes.api_routes import router

app = FastAPI(title="Gestión de Empleados y Pañol")


@app.exception_handler(ResponseValidationError)
async def manejar_error_validacion(request: Request, exc: ResponseValidationError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error de datos: {exc.errors()}"},
    )


@app.exception_handler(Exception)
async def manejar_error_general(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno ({type(exc).__name__}): {exc}"},
    )


app.include_router(router)
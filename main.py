from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from service.rabbitmq_service import RabbitMQService
from controller.serie_controller import router as serie_router, set_rabbitmq_service
from controller.pacs_controller import router as pacs_router

# Instancia global del servicio
rabbitmq_service = RabbitMQService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Conectar a RabbitMQ
    rabbitmq_service.connect()

    # Inyectar servicio en el controlador
    set_rabbitmq_service(rabbitmq_service)

    yield

    # Shutdown: Cerrar conexión
    rabbitmq_service.disconnect()


app = FastAPI(
    title="Gestor Service",
    description="API para gestionar series y publicarlas en RabbitMQ",
    version="1.0.0",
    lifespan=lifespan
)

# Registrar rutas de los controladores
app.include_router(serie_router)
app.include_router(pacs_router)


@app.get("/")
async def root():
    """Endpoint de verificación de estado del servicio"""
    return {
        "service": "gestor-service",
        "status": "running",
        "rabbitmq": "connected"
    }


@app.get("/health")
async def health_check():
    """Health check del servicio y conexión a RabbitMQ"""
    try:
        if rabbitmq_service.is_connected():
            return {
                "status": "healthy",
                "rabbitmq": "connected"
            }
        else:
            return {
                "status": "unhealthy",
                "rabbitmq": "disconnected"
            }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

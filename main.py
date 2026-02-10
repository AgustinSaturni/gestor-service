from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import os
from service.rabbitmq_service import RabbitMQService
from service.database_service import DatabaseService
from repository.paciente_repository import PacienteRepository
from controller.serie_controller import router as serie_router, set_rabbitmq_service, set_paciente_repository
from controller.pacs_controller import router as pacs_router

# Instancias globales de los servicios
rabbitmq_service = RabbitMQService()
database_service = DatabaseService(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "hippal"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "admin")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Conectar a RabbitMQ y PostgreSQL
    rabbitmq_service.connect()
    database_service.connect()

    # Crear repositorio
    paciente_repository = PacienteRepository(database_service)

    # Inyectar servicios en los controladores
    set_rabbitmq_service(rabbitmq_service)
    set_paciente_repository(paciente_repository)

    yield

    # Shutdown: Cerrar conexiones
    rabbitmq_service.disconnect()
    database_service.disconnect()


app = FastAPI(
    title="Gestor Service",
    description="API para gestionar series y publicarlas en RabbitMQ",
    version="1.0.0",
    lifespan=lifespan
)

# Registrar rutas de los controladores
app.include_router(serie_router)
app.include_router(pacs_router)



@app.get("/health")
async def health_check():
    """Health check del servicio, RabbitMQ y PostgreSQL"""
    try:
        rabbitmq_status = "connected" if rabbitmq_service.is_connected() else "disconnected"
        db_status = "connected" if database_service.is_connected() else "disconnected"

        if rabbitmq_status == "connected" and db_status == "connected":
            return {
                "status": "healthy",
                "rabbitmq": rabbitmq_status,
                "database": db_status
            }
        else:
            return {
                "status": "unhealthy",
                "rabbitmq": rabbitmq_status,
                "database": db_status
            }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

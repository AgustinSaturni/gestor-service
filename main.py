from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import os
from service.rabbitmq_service import RabbitMQService
from service.database_service import DatabaseService
from service.minio_service import MinioService
from repository.paciente_repository import PacienteRepository
from repository.estudio_repository import EstudioRepository
from repository.medicion_repository import MedicionRepository
from controller.serie_controller import router as serie_router, set_rabbitmq_service, set_paciente_repository, set_estudio_repository
from controller.estudio_controller import router as estudio_router, set_estudio_repository as set_estudio_repository_controller, set_medicion_repository_estudio, set_minio_service_estudio
from controller.medicion_controller import router as medicion_router, set_medicion_repository, set_minio_service
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

minio_service = MinioService(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "admin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "admin123"),
    bucket=os.getenv("MINIO_BUCKET", "hippal"),
    public_endpoint=os.getenv("MINIO_PUBLIC_ENDPOINT")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Conectar a RabbitMQ y PostgreSQL
    rabbitmq_service.connect()
    database_service.connect()
    minio_service.connect()

    # Crear repositorios
    paciente_repository = PacienteRepository(database_service)
    estudio_repository = EstudioRepository(database_service)
    medicion_repository = MedicionRepository(database_service)

    # Inyectar servicios en los controladores
    set_rabbitmq_service(rabbitmq_service)
    set_paciente_repository(paciente_repository)
    set_estudio_repository(estudio_repository)
    set_estudio_repository_controller(estudio_repository)
    set_medicion_repository_estudio(medicion_repository)
    set_minio_service_estudio(minio_service)
    set_medicion_repository(medicion_repository)
    set_minio_service(minio_service)

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
app.include_router(estudio_router)
app.include_router(medicion_router)



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

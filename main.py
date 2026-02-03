from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pika
import json
import os
from contextlib import asynccontextmanager

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "series_queue")

# Variable global para la conexión
rabbitmq_connection = None
rabbitmq_channel = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Conectar a RabbitMQ
    global rabbitmq_connection, rabbitmq_channel

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )

    rabbitmq_connection = pika.BlockingConnection(parameters)
    rabbitmq_channel = rabbitmq_connection.channel()

    # Declarar la cola (se crea si no existe)
    rabbitmq_channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    print(f"✓ Conectado a RabbitMQ en {RABBITMQ_HOST}:{RABBITMQ_PORT}")

    yield

    # Shutdown: Cerrar conexión
    if rabbitmq_channel:
        rabbitmq_channel.close()
    if rabbitmq_connection:
        rabbitmq_connection.close()
    print("✓ Conexión a RabbitMQ cerrada")


app = FastAPI(
    title="Gestor Service",
    description="API para gestionar series y publicarlas en RabbitMQ",
    version="1.0.0",
    lifespan=lifespan
)


class SerieRequest(BaseModel):
    serie: str


@app.post("/serie", status_code=201)
async def publish_serie(request: SerieRequest):
    """
    Publica un UUID de serie en RabbitMQ

    Args:
        request: Objeto con el UUID de la serie

    Returns:
        Confirmación de publicación exitosa
    """
    try:
        message = {"serie": request.serie}

        # Publicar mensaje en RabbitMQ
        rabbitmq_channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
                content_type='application/json'
            )
        )

        return {
            "status": "success",
            "message": "Serie publicada en RabbitMQ",
            "data": message
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al publicar en RabbitMQ: {str(e)}"
        )


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
        # Verificar que la conexión está activa
        if rabbitmq_connection and rabbitmq_connection.is_open:
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

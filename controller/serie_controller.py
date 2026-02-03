from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from service.rabbitmq_service import RabbitMQService


router = APIRouter(prefix="/serie", tags=["RabbitMq"])

# Inyección de dependencia del servicio
rabbitmq_service: RabbitMQService = None


def set_rabbitmq_service(service: RabbitMQService):
    """Inyecta el servicio de RabbitMQ en el controlador"""
    global rabbitmq_service
    rabbitmq_service = service


class SerieRequest(BaseModel):
    serie: str


@router.post("", status_code=201)
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

        # Publicar mensaje usando el servicio
        success = rabbitmq_service.publish_message(message)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error al publicar en RabbitMQ"
            )

        return {
            "status": "success",
            "message": "Serie publicada en RabbitMQ",
            "data": message
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from service.rabbitmq_service import RabbitMQService
from repository.paciente_repository import PacienteRepository
from models.paciente import Paciente


router = APIRouter(prefix="/serie", tags=["RabbitMq"])

# Inyección de dependencia de los servicios
rabbitmq_service: RabbitMQService = None
paciente_repository: PacienteRepository = None


def set_rabbitmq_service(service: RabbitMQService):
    """Inyecta el servicio de RabbitMQ en el controlador"""
    global rabbitmq_service
    rabbitmq_service = service


def set_paciente_repository(repository: PacienteRepository):
    """Inyecta el repositorio de Paciente en el controlador"""
    global paciente_repository
    paciente_repository = repository


class SerieRequest(BaseModel):
    serie: str
    patient_id: str
    nombre: str
    apellido: str


@router.post("", status_code=201)
async def publish_serie(request: SerieRequest):
    """
    Guarda/actualiza paciente y publica UUID de serie en RabbitMQ

    Args:
        request: Objeto con el UUID de la serie y datos del paciente

    Returns:
        Confirmación de guardado y publicación exitosa
    """
    try:
        # Crear objeto Paciente
        paciente = Paciente(
            patient_id=request.patient_id,
            nombre=request.nombre,
            apellido=request.apellido
        )

        # Guardar paciente en la base de datos
        paciente_guardado = paciente_repository.insert_or_update(paciente)

        # Preparar mensaje para RabbitMQ
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
            "message": "Paciente guardado y serie publicada en RabbitMQ",
            "data": {
                "paciente_id": paciente_guardado.id,
                "patient_id": paciente_guardado.patient_id,
                "serie": request.serie
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )

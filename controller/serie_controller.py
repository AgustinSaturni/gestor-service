from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from service.rabbitmq_service import RabbitMQService
from repository.paciente_repository import PacienteRepository
from repository.estudio_repository import EstudioRepository
from models.paciente import Paciente
from models.estudio import Estudio


router = APIRouter(prefix="/serie", tags=["RabbitMq"])

# Inyección de dependencia de los servicios
rabbitmq_service: RabbitMQService = None
paciente_repository: PacienteRepository = None
estudio_repository: EstudioRepository = None


def set_rabbitmq_service(service: RabbitMQService):
    """Inyecta el servicio de RabbitMQ en el controlador"""
    global rabbitmq_service
    rabbitmq_service = service


def set_paciente_repository(repository: PacienteRepository):
    """Inyecta el repositorio de Paciente en el controlador"""
    global paciente_repository
    paciente_repository = repository


def set_estudio_repository(repository: EstudioRepository):
    """Inyecta el repositorio de Estudio en el controlador"""
    global estudio_repository
    estudio_repository = repository


class SerieRequest(BaseModel):
    serie: str
    patient_id: str
    nombre: str
    angulos: Optional[List[str]] = None
    descripcion: Optional[str] = None
    instancias: Optional[int] = None


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
            nombre=request.nombre
        )

        # Guardar paciente en la base de datos
        paciente_guardado = paciente_repository.insert_or_update(paciente)

        # Crear estudio con estado Pendiente (id=1)
        estudio = Estudio(
            id_paciente=paciente_guardado.id,
            id_estado=1,
            id_serie=request.serie,
            descripcion=request.descripcion,
            instancias=request.instancias
        )
        estudio_guardado = estudio_repository.insert(estudio)

        # Preparar mensaje para RabbitMQ
        message = {"serie": request.serie, "angulos": request.angulos, "estudio_id": estudio_guardado.id}

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
                "serie": request.serie,
                "estudio_id": estudio_guardado.id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )

import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
from repository.estudio_repository import EstudioRepository
from repository.medicion_repository import MedicionRepository
from service.minio_service import MinioService

router = APIRouter(prefix="/estudios", tags=["Estudios"])

estudio_repository: EstudioRepository = None
medicion_repository: MedicionRepository = None
minio_service: MinioService = None


def set_estudio_repository(repository: EstudioRepository):
    global estudio_repository
    estudio_repository = repository


def set_medicion_repository_estudio(repository: MedicionRepository):
    global medicion_repository
    medicion_repository = repository


def set_minio_service_estudio(service: MinioService):
    global minio_service
    minio_service = service


@router.get("/{patient_id}")
async def get_estudios_by_patient(patient_id: str):
    """
    Obtiene los estudios de un paciente.

    Args:
        patient_id: ID del paciente (PatientID DICOM)

    Returns:
        Lista de estudios del paciente
    """
    try:
        estudios = estudio_repository.get_by_patient_id(patient_id)

        return {
            "total": len(estudios),
            "patient_id": patient_id,
            "estudios": estudios
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


@router.delete("/{estudio_id}")
async def delete_estudio(estudio_id: int):
    """
    Elimina un estudio, su medición y las imágenes asociadas en MinIO.
    """
    try:
        # Obtener claves de imágenes antes de borrar
        claves = medicion_repository.get_imagenes_by_estudio_id(estudio_id)

        # Borrar objetos de MinIO
        for clave in claves:
            try:
                minio_service.eliminar_objeto(clave)
            except Exception as e:
                logger.warning(f"No se pudo eliminar objeto MinIO {clave}: {e}")

        # Borrar medición + estudio via SP
        estudio_repository.delete(estudio_id)

        return {"message": f"Estudio {estudio_id} eliminado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar estudio: {str(e)}"
        )

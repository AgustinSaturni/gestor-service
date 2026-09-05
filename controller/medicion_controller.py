from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any
from repository.medicion_repository import MedicionRepository
from service.minio_service import MinioService

router = APIRouter(prefix="/mediciones", tags=["Mediciones"])

medicion_repository: MedicionRepository = None
minio_service: MinioService = None


def set_medicion_repository(repository: MedicionRepository):
    global medicion_repository
    medicion_repository = repository


def set_minio_service(service: MinioService):
    global minio_service
    minio_service = service


@router.get("/{estudio_id}")
async def get_medicion_by_estudio(estudio_id: int):
    """
    Obtiene los resultados de medicion de un estudio.
    """
    try:
        medicion = medicion_repository.get_by_estudio_id(estudio_id)

        if not medicion:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron mediciones para el estudio {estudio_id}"
            )

        return medicion

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


class CorreccionesPayload(BaseModel):
    correcciones: dict[str, Any]


@router.patch("/{estudio_id}")
async def save_correcciones(estudio_id: int, payload: CorreccionesPayload):
    """
    Guarda o reemplaza las correcciones manuales de los ángulos de un estudio.
    Las correcciones siguen la misma estructura que 'resultados' pero solo
    incluyen los campos que el usuario corrigió.
    """
    try:
        medicion_repository.save_correcciones(estudio_id, payload.correcciones)
        return {"message": f"Correcciones guardadas para estudio {estudio_id}"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar correcciones: {str(e)}"
        )


@router.get("/{estudio_id}/imagen")
async def get_imagen_url(estudio_id: int, clave: str = Query(..., description="Clave del objeto en MinIO")):
    """
    Genera una URL prefirmada para acceder a una imagen de la medicion.
    """
    try:
        url = minio_service.generar_url_publica(clave)
        return {"url": url}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar URL: {str(e)}"
        )

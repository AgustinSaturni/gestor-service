from fastapi import APIRouter, HTTPException, Query
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

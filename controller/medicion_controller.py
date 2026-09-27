from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from minio.error import S3Error
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


class ResultadosPayload(BaseModel):
    resultados: dict[str, Any]


@router.patch("/{estudio_id}")
async def update_resultados(estudio_id: int, payload: ResultadosPayload):
    """
    Reemplaza los resultados de un estudio con los valores corregidos por el usuario.
    El frontend envía el dict completo de resultados con las correcciones ya aplicadas.
    """
    try:
        medicion_repository.update_resultados(estudio_id, payload.resultados)
        return {"message": f"Resultados actualizados para estudio {estudio_id}"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar resultados: {str(e)}"
        )


@router.get("/{estudio_id}/imagen")
async def get_imagen(estudio_id: int, clave: str = Query(..., description="Clave del objeto en MinIO")):
    """
    Devuelve la imagen de la medicion.

    Actua de proxy para que MinIO no tenga que ser alcanzable desde el
    navegador: antes este endpoint devolvia una URL directa al puerto de MinIO,
    lo que obligaba a publicarlo y a dejar el bucket con acceso anonimo. Ahora
    el unico puerto publico es este, igual que con Orthanc en pacs_controller.

    La clave se valida contra las imagenes del estudio para que el path param
    signifique algo: sin eso el endpoint servia cualquier objeto del bucket.
    """
    try:
        if clave not in medicion_repository.get_imagenes_by_estudio_id(estudio_id):
            raise HTTPException(
                status_code=404,
                detail=f"La imagen no pertenece al estudio {estudio_id}"
            )

        chunks, content_type = minio_service.stream_objeto(clave)

        return StreamingResponse(
            chunks,
            media_type=content_type,
            # La imagen de un angulo no cambia una vez generada: las correcciones
            # manuales solo reescriben puntos y angulos, y las rectas las dibuja
            # el front encima. private porque son imagenes de un paciente.
            headers={"Cache-Control": "private, max-age=3600"}
        )

    except HTTPException:
        raise
    except S3Error as e:
        raise HTTPException(
            status_code=404 if e.code == "NoSuchKey" else 502,
            detail=f"Error al leer la imagen de MinIO: {e.code}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener la imagen: {str(e)}"
        )

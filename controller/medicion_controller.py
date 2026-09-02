from fastapi import APIRouter, HTTPException
from repository.medicion_repository import MedicionRepository

router = APIRouter(prefix="/mediciones", tags=["Mediciones"])

medicion_repository: MedicionRepository = None


def set_medicion_repository(repository: MedicionRepository):
    """Inyecta el repositorio de Medicion en el controlador"""
    global medicion_repository
    medicion_repository = repository


@router.get("/{estudio_id}")
async def get_medicion_by_estudio(estudio_id: int):
    """
    Obtiene los resultados de medicion de un estudio.

    Args:
        estudio_id: ID del estudio

    Returns:
        Resultados de la medicion (JSONB)
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

from fastapi import APIRouter, HTTPException
import requests
from service.orthanc_service import OrthancService


router = APIRouter(prefix="/api/pacs", tags=["PACS"])

# Instancia del servicio Orthanc
orthanc_service = OrthancService()


@router.get("/series")
async def get_series_pacs():
    """
    Lista todas las series disponibles en el PACS con sus UUIDs.

    Returns:
        Diccionario con el total de series y la lista completa
    """
    try:
        series = orthanc_service.list_all_series()

        return {
            "total": len(series),
            "series": series
        }

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar al servidor PACS (Orthanc)"
        )
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error del servidor PACS: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )

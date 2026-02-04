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


@router.get("/patients/search")
async def search_patients(nombre: str, apellido: str):
    """
    Busca pacientes en el PACS que coincidan con nombre y apellido.
    Devuelve una lista de pacientes únicos para que el usuario pueda elegir.

    Args:
        nombre: Nombre del paciente
        apellido: Apellido del paciente

    Returns:
        Diccionario con pacientes encontrados y sus datos (PatientID, nombre, cantidad de estudios)
    """
    try:
        patients = orthanc_service.search_patients_by_name(nombre, apellido)

        return {
            "total": len(patients),
            "patients": patients,
            "search_params": {
                "nombre": nombre,
                "apellido": apellido
            }
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


@router.get("/patients/{patient_id}/series")
async def get_patient_series(patient_id: str):
    """
    Obtiene todas las series de un paciente específico usando su PatientID.

    Args:
        patient_id: ID del paciente (PatientID DICOM)

    Returns:
        Diccionario con las series del paciente
    """
    try:
        series = orthanc_service.get_series_by_patient_id(patient_id)

        if not series:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron series para el paciente con ID: {patient_id}"
            )

        return {
            "total": len(series),
            "patient_id": patient_id,
            "series": series
        }

    except HTTPException:
        raise
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

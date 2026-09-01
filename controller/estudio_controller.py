from fastapi import APIRouter, HTTPException
from repository.estudio_repository import EstudioRepository

router = APIRouter(prefix="/estudios", tags=["Estudios"])

estudio_repository: EstudioRepository = None


def set_estudio_repository(repository: EstudioRepository):
    """Inyecta el repositorio de Estudio en el controlador"""
    global estudio_repository
    estudio_repository = repository


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

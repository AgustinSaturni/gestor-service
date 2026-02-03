import os
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any, Optional


class OrthancService:
    """
    Servicio para interactuar con el servidor PACS Orthanc
    """

    def __init__(self):
        self.url = os.getenv("ORTHANC_URL", "http://localhost:8042")
        self.user = os.getenv("ORTHANC_USER", "admin")
        self.password = os.getenv("ORTHANC_PASSWORD", "admin")
        self.auth = HTTPBasicAuth(self.user, self.password)

    def _get(self, endpoint: str) -> Any:
        """
        Realiza una petición GET al servidor Orthanc

        Args:
            endpoint: Ruta del endpoint (sin la URL base)

        Returns:
            Respuesta JSON del servidor
        """
        response = requests.get(f"{self.url}{endpoint}", auth=self.auth)
        response.raise_for_status()
        return response.json()

    def get_all_studies(self) -> List[str]:
        """
        Obtiene todos los IDs de estudios disponibles en el PACS

        Returns:
            Lista de IDs de estudios
        """
        return self._get("/studies")

    def get_study_info(self, study_id: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un estudio

        Args:
            study_id: ID del estudio

        Returns:
            Diccionario con información del estudio
        """
        return self._get(f"/studies/{study_id}")

    def get_study_series(self, study_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las series de un estudio

        Args:
            study_id: ID del estudio

        Returns:
            Lista de series con su información
        """
        return self._get(f"/studies/{study_id}/series")

    def list_all_series(self) -> List[Dict[str, Any]]:
        """
        Lista todas las series disponibles en el PACS con información detallada

        Returns:
            Lista de diccionarios con información de cada serie
        """
        result = []
        studies = self.get_all_studies()

        for study_id in studies:
            study_info = self.get_study_info(study_id)
            patient_name = study_info.get("PatientMainDicomTags", {}).get(
                "PatientName", "Desconocido"
            )

            series_list = self.get_study_series(study_id)

            for series_info in series_list:
                main_tags = series_info.get("MainDicomTags", {})
                result.append({
                    "uuid": series_info.get("ID"),
                    "patient_name": patient_name,
                    "study_id": study_id,
                    "series_number": main_tags.get("SeriesNumber", "N/A"),
                    "description": main_tags.get("SeriesDescription", "Sin descripción"),
                    "modality": main_tags.get("Modality", "Desconocida"),
                    "num_instances": len(series_info.get("Instances", []))
                })

        return result

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

    def search_patients_by_name(self, nombre: str, apellido: str) -> List[Dict[str, Any]]:
        """
        Busca pacientes que coincidan con nombre y apellido

        Args:
            nombre: Nombre del paciente
            apellido: Apellido del paciente

        Returns:
            Lista de pacientes únicos con su información
        """
        patients_dict = {}
        studies = self.get_all_studies()

        # Normalizar búsqueda (convertir a minúsculas para comparación)
        nombre_lower = nombre.lower().strip()
        apellido_lower = apellido.lower().strip()

        for study_id in studies:
            study_info = self.get_study_info(study_id)
            patient_tags = study_info.get("PatientMainDicomTags", {})
            patient_name = patient_tags.get("PatientName", "")
            patient_id = patient_tags.get("PatientID", "")

            # DICOM PatientName suele tener formato "APELLIDO^NOMBRE"
            # Normalizar y comparar
            patient_name_lower = patient_name.lower()

            # Verificar si coincide con el patrón "APELLIDO^NOMBRE" o si contiene ambos
            if (f"{apellido_lower}^{nombre_lower}" in patient_name_lower or
                (apellido_lower in patient_name_lower and nombre_lower in patient_name_lower)):

                # Agrupar por PatientID para evitar duplicados
                if patient_id not in patients_dict:
                    patients_dict[patient_id] = {
                        "patient_id": patient_id,
                        "patient_name": patient_name,
                        "num_studies": 0,
                        "study_ids": []
                    }

                patients_dict[patient_id]["num_studies"] += 1
                patients_dict[patient_id]["study_ids"].append(study_id)

        return list(patients_dict.values())

    def get_series_by_patient_id(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las series de un paciente específico usando su PatientID

        Args:
            patient_id: ID del paciente (PatientID DICOM)

        Returns:
            Lista de series del paciente
        """
        result = []
        studies = self.get_all_studies()

        for study_id in studies:
            study_info = self.get_study_info(study_id)
            patient_tags = study_info.get("PatientMainDicomTags", {})
            current_patient_id = patient_tags.get("PatientID", "")
            patient_name = patient_tags.get("PatientName", "Desconocido")

            if current_patient_id == patient_id:
                series_list = self.get_study_series(study_id)

                for series_info in series_list:
                    main_tags = series_info.get("MainDicomTags", {})
                    result.append({
                        "uuid": series_info.get("ID"),
                        "patient_id": patient_id,
                        "patient_name": patient_name,
                        "study_id": study_id,
                        "series_number": main_tags.get("SeriesNumber", "N/A"),
                        "description": main_tags.get("SeriesDescription", "Sin descripción"),
                        "modality": main_tags.get("Modality", "Desconocida"),
                        "num_instances": len(series_info.get("Instances", []))
                    })

        return result

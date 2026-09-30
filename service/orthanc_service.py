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

    def _post(self, endpoint: str, payload: Any) -> Any:
        """
        Realiza una peticion POST al servidor Orthanc

        Args:
            endpoint: Ruta del endpoint (sin la URL base)
            payload: Cuerpo JSON de la peticion

        Returns:
            La respuesta decodificada
        """
        response = requests.post(f"{self.url}{endpoint}", auth=self.auth, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _origen_desde_image_type(image_type: Any) -> Optional[str]:
        """
        Traduce el tag ImageType a 'Original' o 'Derivada'.

        Su primer valor es ORIGINAL o DERIVED. Importa al elegir que serie
        analizar: una reconstruccion MPR de la estacion puede venir con cortes
        vacios que la adquisicion original no tiene, y desde la descripcion no
        hay forma de distinguirlas.
        """
        if not image_type:
            return None
        primero = str(image_type).split("\\")[0].strip().upper()
        if primero == "ORIGINAL":
            return "Original"
        if primero == "DERIVED":
            return "Derivada"
        return None

    def get_series_instances(self, series_id: str) -> List[Dict[str, Any]]:
        """
        Lista las instancias de una serie, ordenadas anatomicamente.

        Orthanc devuelve las instancias sin un orden garantizado, asi que se
        ordenan por InstanceNumber. Las que no lo tengan caen al final, en el
        orden que Orthanc les haya asignado.

        Una sola llamada trae los tags de todas las instancias, asi que esto no
        escala con la cantidad de cortes.

        Args:
            series_id: UUID de la serie en Orthanc

        Returns:
            Lista de dicts con id y numero de instancia
        """
        instancias = self._get(f"/series/{series_id}/instances")

        def clave_orden(inst: Dict[str, Any]):
            numero = inst.get("MainDicomTags", {}).get("InstanceNumber")
            try:
                return (0, int(numero))
            except (TypeError, ValueError):
                return (1, inst.get("IndexInSeries") or 0)

        instancias.sort(key=clave_orden)

        return [
            {
                "id": inst.get("ID"),
                "instance_number": inst.get("MainDicomTags", {}).get("InstanceNumber"),
            }
            for inst in instancias
        ]

    def get_instance_preview(self, instance_id: str, width: Optional[int] = None):
        """
        Obtiene el corte renderizado como imagen, sin descargarlo en memoria.

        Devuelve la respuesta de requests en modo stream para que el controller
        la reenvie por chunks: con cientos de cortes no conviene bufferear cada
        imagen entera antes de responder.

        Args:
            instance_id: UUID de la instancia en Orthanc
            width: Ancho en pixeles para que Orthanc reescale del lado del
                   servidor. Sin esto devuelve la resolucion original.

        Returns:
            requests.Response en modo stream
        """
        if width:
            endpoint = f"/instances/{instance_id}/rendered"
            params = {"width": width}
        else:
            endpoint = f"/instances/{instance_id}/preview"
            params = None

        response = requests.get(
            f"{self.url}{endpoint}", auth=self.auth, params=params, stream=True
        )
        response.raise_for_status()
        return response

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

    def get_series_origen(self, series_id: str) -> Optional[str]:
        """
        Indica si la serie es la adquisicion original o una reconstruccion.

        ImageType es un tag de instancia, no de serie, pero es el mismo en todos
        los cortes: shared-tags lo resuelve en una llamada en vez de una por
        corte. Su primer valor es ORIGINAL o DERIVED.

        Importa al elegir que serie analizar: una reconstruccion MPR de la
        estacion puede venir con cortes vacios que la adquisicion original no
        tiene, y desde la descripcion no hay forma de distinguirlas.

        Args:
            series_id: UUID de la serie en Orthanc

        Returns:
            'Original', 'Derivada', o None si la serie no declara ImageType
        """
        try:
            tags = self._get(f"/series/{series_id}/shared-tags?simplify")
        except Exception:
            return None
        return self._origen_desde_image_type(tags.get("ImageType"))

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

        Resuelve la busqueda en Orthanc con /tools/find en vez de recorrer el
        PACS entero. Antes esto pedia la lista completa de estudios, consultaba
        cada uno para ver de quien era, y por cada serie del paciente hacia otra
        llamada para el origen: el costo crecia con el tamaño del PACS aunque el
        paciente tuviera dos series. Con 25 estudios ya tardaba 16-22 segundos;
        ahora es una sola peticion.

        Args:
            patient_id: ID del paciente (PatientID DICOM)

        Returns:
            Lista de series del paciente
        """
        series = self._post("/tools/find", {
            "Level": "Series",
            "Query": {"PatientID": patient_id},
            "Expand": True,
            # ImageType es un tag de instancia, pero es el mismo en todos los
            # cortes y Orthanc lo resuelve aca: evita una llamada por serie.
            "RequestedTags": ["PatientName", "ImageType"],
        })

        result = []
        for series_info in series:
            main_tags = series_info.get("MainDicomTags", {})
            requested = series_info.get("RequestedTags", {})
            result.append({
                "uuid": series_info.get("ID"),
                "patient_id": patient_id,
                "patient_name": requested.get("PatientName", "Desconocido"),
                "study_id": series_info.get("ParentStudy"),
                "series_number": main_tags.get("SeriesNumber", "N/A"),
                "description": main_tags.get("SeriesDescription", "Sin descripción"),
                "modality": main_tags.get("Modality", "Desconocida"),
                "num_instances": len(series_info.get("Instances", [])),
                "origen": self._origen_desde_image_type(requested.get("ImageType")),
            })

        return result

import logging
from models.estudio import Estudio
from service.database_service import DatabaseService

logger = logging.getLogger(__name__)


class EstudioRepository:
    """Repository para operaciones de Estudio en la base de datos"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service

    def insert(self, estudio: Estudio) -> Estudio:
        """
        Inserta un nuevo estudio en la base de datos.

        Args:
            estudio: Objeto Estudio a insertar

        Returns:
            Estudio con el ID asignado por la base de datos
        """
        connection = None
        try:
            connection = self.database_service.get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO estudio (id_paciente, id_estado, id_serie, descripcion, instancias) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (estudio.id_paciente, estudio.id_estado, estudio.id_serie, estudio.descripcion, estudio.instancias)
            )

            result = cursor.fetchone()
            estudio.id = result[0]

            connection.commit()
            cursor.close()

            logger.info(f"Estudio creado exitosamente: {estudio}")
            return estudio

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Error al crear estudio: {e}")
            raise

        finally:
            if connection:
                self.database_service.return_connection(connection)

    def get_by_patient_id(self, patient_id: str) -> list[dict]:
        """
        Obtiene los estudios de un paciente usando la vista v_estudios.

        Args:
            patient_id: ID del paciente (PatientID DICOM)

        Returns:
            Lista de estudios del paciente
        """
        connection = None
        try:
            connection = self.database_service.get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT estudio_id, patient_id, paciente, estado, id_serie, descripcion, instancias, created_at FROM v_estudios WHERE patient_id = %s",
                (patient_id,)
            )

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            estudios = [dict(zip(columns, row)) for row in rows]

            cursor.close()
            return estudios

        except Exception as e:
            logger.error(f"Error al obtener estudios del paciente {patient_id}: {e}")
            raise

        finally:
            if connection:
                self.database_service.return_connection(connection)

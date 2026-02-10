import logging
from models.paciente import Paciente
from service.database_service import DatabaseService

logger = logging.getLogger(__name__)


class PacienteRepository:
    """Repository para operaciones de Paciente en la base de datos"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service

    def insert_or_update(self, paciente: Paciente) -> Paciente:
        """
        Inserta un paciente en la base de datos si no existe.
        Si ya existe, retorna el ID existente sin hacer cambios.
        Retorna el objeto Paciente con el ID asignado.

        Args:
            paciente: Objeto Paciente a insertar

        Returns:
            Paciente con el ID asignado por la base de datos

        Raises:
            Exception: Si ocurre un error en la operación
        """
        connection = None
        try:
            connection = self.database_service.get_connection()
            cursor = connection.cursor()

            # Llamar al stored procedure
            cursor.execute(
                "SELECT upsert_paciente(%s, %s, %s)",
                (paciente.patient_id, paciente.nombre, paciente.apellido)
            )

            # Obtener el ID retornado
            result = cursor.fetchone()
            paciente.id = result[0]

            connection.commit()
            cursor.close()

            logger.info(f"Paciente procesado exitosamente: {paciente}")
            return paciente

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Error al procesar paciente: {e}")
            raise

        finally:
            if connection:
                self.database_service.return_connection(connection)

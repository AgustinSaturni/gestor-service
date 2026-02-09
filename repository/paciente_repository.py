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
        Inserta o actualiza un paciente en la base de datos.
        Retorna el objeto Paciente con el ID asignado.

        Args:
            paciente: Objeto Paciente a insertar/actualizar

        Returns:
            Paciente con el ID asignado por la base de datos

        Raises:
            Exception: Si ocurre un error en la operación
        """
        connection = None
        try:
            connection = self.database_service.get_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO paciente (patient_id, nombre, apellido)
                VALUES (%s, %s, %s)
                ON CONFLICT (patient_id)
                DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    apellido = EXCLUDED.apellido
                RETURNING id;
            """

            cursor.execute(query, (
                paciente.patient_id,
                paciente.nombre,
                paciente.apellido
            ))

            # Obtener el ID retornado
            result = cursor.fetchone()
            paciente.id = result[0]

            connection.commit()
            cursor.close()

            logger.info(f"Paciente guardado exitosamente: {paciente}")
            return paciente

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Error al guardar paciente: {e}")
            raise

        finally:
            if connection:
                self.database_service.return_connection(connection)

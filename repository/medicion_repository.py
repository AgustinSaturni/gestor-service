import logging
from service.database_service import DatabaseService

logger = logging.getLogger(__name__)


class MedicionRepository:
    """Repository para operaciones de Medicion en la base de datos"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service

    def get_by_estudio_id(self, estudio_id: int) -> dict | None:
        """
        Obtiene la medicion de un estudio.

        Args:
            estudio_id: ID del estudio

        Returns:
            Dict con id, estudio_id y resultados (JSONB), o None si no existe
        """
        connection = None
        try:
            connection = self.database_service.get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT id, estudio_id, resultados, created_at FROM medicion WHERE estudio_id = %s",
                (estudio_id,)
            )

            row = cursor.fetchone()
            cursor.close()

            if row:
                return {
                    "id": row[0],
                    "estudio_id": row[1],
                    "resultados": row[2],
                    "created_at": row[3].isoformat() if row[3] else None
                }
            return None

        except Exception as e:
            logger.error(f"Error al obtener medicion del estudio {estudio_id}: {e}")
            raise

        finally:
            if connection:
                self.database_service.return_connection(connection)

    def update_resultados(self, estudio_id: int, resultados: dict) -> None:
        """
        Reemplaza los resultados de un estudio con los valores corregidos por el usuario.

        Args:
            estudio_id: ID del estudio
            resultados: Dict completo de resultados con correcciones aplicadas
        """
        import json
        connection = None
        try:
            connection = self.database_service.get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "UPDATE medicion SET resultados = %s WHERE estudio_id = %s",
                (json.dumps(resultados), estudio_id)
            )

            if cursor.rowcount == 0:
                raise ValueError(f"No existe medicion para el estudio {estudio_id}")

            connection.commit()
            cursor.close()
            logger.info(f"Resultados actualizados para estudio {estudio_id}")

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Error al actualizar resultados del estudio {estudio_id}: {e}")
            raise

        finally:
            if connection:
                self.database_service.return_connection(connection)

    def get_imagenes_by_estudio_id(self, estudio_id: int) -> list[str]:
        """
        Obtiene las claves de imágenes en MinIO de un estudio.

        Returns:
            Lista de claves (paths) de objetos en MinIO
        """
        connection = None
        try:
            connection = self.database_service.get_connection()
            cursor = connection.cursor()

            cursor.execute(
                "SELECT resultados->'imagenes' FROM medicion WHERE estudio_id = %s",
                (estudio_id,)
            )

            row = cursor.fetchone()
            cursor.close()

            if row and row[0]:
                return list(row[0].values())
            return []

        except Exception as e:
            logger.error(f"Error al obtener imágenes del estudio {estudio_id}: {e}")
            raise

        finally:
            if connection:
                self.database_service.return_connection(connection)

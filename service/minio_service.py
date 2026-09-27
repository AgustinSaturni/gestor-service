import logging
from minio import Minio

logger = logging.getLogger(__name__)


class MinioService:
    """Servicio de acceso a las imagenes de mediciones guardadas en MinIO"""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "admin",
        secret_key: str = "admin123",
        bucket: str = "hippal",
        secure: bool = False
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self.client = None

    def connect(self):
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        logger.info(f"Cliente MinIO conectado: {self.endpoint}")

    def eliminar_objeto(self, clave: str) -> None:
        """Elimina un objeto del bucket de MinIO."""
        self.client.remove_object(self.bucket, clave)
        logger.info(f"Objeto eliminado de MinIO: {clave}")

    def stream_objeto(self, clave: str, chunk_size: int = 65536):
        """
        Abre un objeto del bucket y devuelve (generador_de_chunks, content_type).

        El backend reenvia los bytes en vez de dar una URL al navegador para que
        MinIO no necesite ser alcanzable desde afuera: queda solo en la red
        interna, igual que Postgres, y el bucket no necesita acceso anonimo.
        Es el mismo criterio que el proxy de Orthanc en pacs_controller.

        get_object abre la conexion de entrada, asi que una clave inexistente
        levanta S3Error aca y no a mitad del streaming. El generador libera la
        conexion al terminar; sin eso el pool de urllib3 se agota.
        """
        respuesta = self.client.get_object(self.bucket, clave)
        content_type = respuesta.headers.get("Content-Type", "application/octet-stream")

        def generador():
            try:
                yield from respuesta.stream(chunk_size)
            finally:
                respuesta.close()
                respuesta.release_conn()

        return generador(), content_type

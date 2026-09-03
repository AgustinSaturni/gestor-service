import logging
from minio import Minio

logger = logging.getLogger(__name__)


class MinioService:
    """Servicio para generar URLs prefirmadas de imágenes en MinIO"""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "admin",
        secret_key: str = "admin123",
        bucket: str = "hippal",
        secure: bool = False,
        public_endpoint: str = None
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self.public_endpoint = public_endpoint
        self.client = None

    def connect(self):
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        logger.info(f"Cliente MinIO conectado: {self.endpoint}")

    def generar_url_publica(self, clave: str) -> str:
        """Genera una URL pública directa (requiere bucket con acceso anónimo)."""
        scheme = "https" if self.secure else "http"
        endpoint = self.public_endpoint or self.endpoint
        return f"{scheme}://{endpoint}/{self.bucket}/{clave}"

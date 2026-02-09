import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Servicio para manejar la conexión a PostgreSQL"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "hippal",
        user: str = "admin",
        password: str = "admin",
        minconn: int = 1,
        maxconn: int = 10
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.minconn = minconn
        self.maxconn = maxconn
        self.connection_pool = None

    def connect(self):
        """Inicializa el pool de conexiones"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                self.minconn,
                self.maxconn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Pool de conexiones PostgreSQL creado: {self.database}@{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error al crear pool de conexiones PostgreSQL: {e}")
            raise

    def disconnect(self):
        """Cierra el pool de conexiones"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Pool de conexiones PostgreSQL cerrado")

    def get_connection(self):
        """Obtiene una conexión del pool"""
        if not self.connection_pool:
            raise Exception("Pool de conexiones no inicializado")
        return self.connection_pool.getconn()

    def return_connection(self, connection):
        """Devuelve una conexión al pool"""
        if self.connection_pool:
            self.connection_pool.putconn(connection)

    def is_connected(self) -> bool:
        """Verifica si el pool está activo"""
        return self.connection_pool is not None

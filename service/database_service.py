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

    @staticmethod
    def _conexion_viva(conexion) -> bool:
        """
        Comprueba que la conexion sirva antes de entregarla.

        El pool guarda las conexiones y las reparte, pero no se entera si del
        otro lado se murieron. Cuando Postgres se reinicia, las que quedaron
        guardadas siguen en el pool y getconn las devuelve igual: el primer uso
        falla con "connection already closed" y el servicio queda inutil hasta
        que se lo reinicia a mano.
        """
        if conexion.closed:
            return False
        try:
            conexion.rollback()  # descarta una transaccion que haya quedado cortada
            with conexion.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except psycopg2.Error:
            return False

    def get_connection(self):
        """Obtiene una conexión del pool, descartando las que ya no sirven"""
        if not self.connection_pool:
            raise Exception("Pool de conexiones no inicializado")

        for _ in range(self.maxconn + 1):
            conexion = self.connection_pool.getconn()
            if self._conexion_viva(conexion):
                return conexion
            # close=True la saca del pool; la proxima vuelta getconn abre una nueva
            logger.warning("Conexión muerta descartada del pool, se abre otra")
            self.connection_pool.putconn(conexion, close=True)

        # Ninguna servia: el pool entero quedo viejo, se rehace
        logger.warning("Todas las conexiones del pool estaban muertas, se recrea el pool")
        self.connect()
        return self.connection_pool.getconn()

    def return_connection(self, connection):
        """Devuelve una conexión al pool"""
        if self.connection_pool:
            self.connection_pool.putconn(connection)

    def is_connected(self) -> bool:
        """Verifica si el pool está activo"""
        return self.connection_pool is not None

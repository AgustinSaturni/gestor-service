import pika
import json
import os
from typing import Dict, Any


class RabbitMQService:
    """
    Servicio para manejar la conexión y publicación de mensajes en RabbitMQ
    """

    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.user = os.getenv("RABBITMQ_USER", "admin")
        self.password = os.getenv("RABBITMQ_PASSWORD", "admin")
        self.queue = os.getenv("RABBITMQ_QUEUE", "series_queue")

        self.connection = None
        self.channel = None

    def connect(self):
        """Establece conexión con RabbitMQ con heartbeat para mantenerla activa"""
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,  # Heartbeat cada 10 minutos
            blocked_connection_timeout=300,  # Timeout de 5 minutos
        )

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # Declarar la cola (se crea si no existe)
        self.channel.queue_declare(queue=self.queue, durable=True)

        print(f"✓ Conectado a RabbitMQ en {self.host}:{self.port}")

    def disconnect(self):
        """Cierra la conexión con RabbitMQ"""
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()
        print("✓ Conexión a RabbitMQ cerrada")

    def _ensure_connection(self):
        """Asegura que la conexión esté activa, reconectando si es necesario"""
        if not self.is_connected():
            print("⚠ Conexión perdida, reconectando...")
            self.connect()

    def publish_message(self, message: Dict[str, Any]) -> bool:
        """
        Publica un mensaje en RabbitMQ con reconexión automática

        Args:
            message: Diccionario con el mensaje a publicar

        Returns:
            True si se publicó correctamente, False en caso contrario
        """
        try:
            # Verificar y reconectar si es necesario
            self._ensure_connection()

            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json'
                )
            )
            return True
        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError,
                pika.exceptions.ConnectionClosedByBroker) as e:
            print(f"⚠ Error de conexión: {str(e)}, reintentando...")
            try:
                # Intentar reconectar y publicar nuevamente
                self.connect()
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                print("✓ Mensaje publicado tras reconexión")
                return True
            except Exception as retry_error:
                print(f"✗ Error al reintentar: {str(retry_error)}")
                return False
        except Exception as e:
            print(f"✗ Error al publicar mensaje: {str(e)}")
            return False

    def is_connected(self) -> bool:
        """Verifica si la conexión y el canal están activos"""
        return (self.connection is not None and
                self.connection.is_open and
                self.channel is not None and
                self.channel.is_open)

# Gestor Service

Backend API que gestiona la interacción del usuario con el servidor PACS (Orthanc), persiste datos en PostgreSQL y produce mensajes a RabbitMQ para iniciar el procesamiento de tomografías.

## Stack Tecnológico

- **FastAPI** con Uvicorn
- **PostgreSQL** (psycopg2) con connection pooling
- **RabbitMQ** (pika) para mensajería asíncrona
- **Orthanc** como servidor PACS (DICOM)
- **Python 3.11**

## Endpoints

### PACS (`/api/pacs`)

| Método | Ruta                              | Descripción                                      |
|--------|-----------------------------------|--------------------------------------------------|
| GET    | `/api/pacs/series`                | Lista todas las series disponibles en el PACS    |
| GET    | `/api/pacs/patients/search`       | Busca pacientes por nombre en Orthanc            |
| GET    | `/api/pacs/patients/{id}/series`  | Obtiene las series de un paciente específico      |

### Series (`/serie`)

| Método | Ruta     | Descripción                                                                 |
|--------|----------|-----------------------------------------------------------------------------|
| POST   | `/serie` | Guarda/actualiza paciente, crea estudio (Pendiente) y publica en RabbitMQ   |

El body del POST incluye: `serie`, `patient_id`, `nombre`, `angulos`, `descripcion`, `instancias`.

### Estudios (`/estudios`)

| Método | Ruta                     | Descripción                                          |
|--------|--------------------------|------------------------------------------------------|
| GET    | `/estudios/{patient_id}` | Obtiene estudios de un paciente desde la vista `v_estudios` |

### Health (`/health`)

| Método | Ruta      | Descripción                                    |
|--------|-----------|-------------------------------------------------|
| GET    | `/health` | Estado del servicio, RabbitMQ y PostgreSQL       |

## Arquitectura

```
main.py                          # App FastAPI, lifespan, inyección de dependencias
controller/
├── pacs_controller.py           # Proxy a Orthanc (búsqueda, series)
├── serie_controller.py          # POST serie → DB + RabbitMQ
└── estudio_controller.py        # GET estudios por paciente
service/
├── orthanc_service.py           # Cliente HTTP para Orthanc
├── rabbitmq_service.py          # Conexión y publicación en RabbitMQ (con reconexión)
└── database_service.py          # Pool de conexiones PostgreSQL
models/
├── paciente.py                  # Modelo: id, patient_id, nombre
└── estudio.py                   # Modelo: id, id_paciente, id_estado, id_serie, descripcion, instancias
repository/
├── paciente_repository.py       # insert_or_update via stored procedure upsert_paciente
└── estudio_repository.py        # insert (RETURNING id), get_by_patient_id (vista v_estudios)
```

## Base de Datos

### Tablas

- **paciente**: id, patient_id (DICOM), nombre, created_at
- **estado**: id, nombre (Pendiente, Procesando, Finalizado, Error)
- **estudio**: id, id_paciente (FK), id_estado (FK), id_serie, descripcion, instancias

### Vista

- **v_estudios**: JOIN entre estudio, paciente y estado. Columnas: estudio_id, patient_id, paciente, estado, id_serie, descripcion, instancias

### Stored Procedure

- **upsert_paciente(p_patient_id, p_nombre)**: Inserta o actualiza un paciente por patient_id

## Variables de Entorno

| Variable       | Descripción                | Default       |
|----------------|----------------------------|---------------|
| `DB_HOST`      | Host de PostgreSQL         | `localhost`   |
| `DB_PORT`      | Puerto de PostgreSQL       | `5432`        |
| `DB_NAME`      | Nombre de la base de datos | `hippal`      |
| `DB_USER`      | Usuario de PostgreSQL      | `admin`       |
| `DB_PASSWORD`  | Contraseña de PostgreSQL   | `admin`       |
| `RABBITMQ_HOST`| Host de RabbitMQ           | `localhost`   |
| `ORTHANC_URL`  | URL del servidor Orthanc   | `http://localhost:8042` |

## Desarrollo

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Documentación interactiva en [http://localhost:8000/docs](http://localhost:8000/docs).

## Docker

```bash
docker build -t gestor-service .
docker run -p 8000:8000 gestor-service
```

El contenedor expone el puerto `8000`.

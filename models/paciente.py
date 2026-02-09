from typing import Optional


class Paciente:
    """Modelo de dominio para Paciente"""

    def __init__(
        self,
        patient_id: str,
        nombre: str,
        apellido: str,
        id: Optional[int] = None
    ):
        self.id = id
        self.patient_id = patient_id
        self.nombre = nombre
        self.apellido = apellido

    def __repr__(self):
        return f"Paciente(id={self.id}, patient_id='{self.patient_id}', nombre='{self.nombre}', apellido='{self.apellido}')"

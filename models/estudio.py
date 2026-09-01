from typing import Optional


class Estudio:
    """Modelo de dominio para Estudio"""

    def __init__(
        self,
        id_paciente: int,
        id_estado: int,
        id_serie: str,
        descripcion: Optional[str] = None,
        instancias: Optional[int] = None,
        id: Optional[int] = None
    ):
        self.id = id
        self.id_paciente = id_paciente
        self.id_estado = id_estado
        self.id_serie = id_serie
        self.descripcion = descripcion
        self.instancias = instancias

    def __repr__(self):
        return f"Estudio(id={self.id}, id_paciente={self.id_paciente}, id_estado={self.id_estado}, id_serie='{self.id_serie}')"

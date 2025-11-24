from pyswip import Prolog
from typing import Optional
import os


class PrologService:
    """
    Servicio para manejar consultas al sistema Prolog.
    """

    def __init__(self, prolog_file_path: str = "prolog/plant_diagnostics.pl"):
        """
        Inicializa el servicio de Prolog.

        Args:
            prolog_file_path: Ruta al archivo .pl
        """
        self.prolog_file_path = prolog_file_path
        self._prolog = None

    def _initialize_prolog(self):
        """
        Inicializa y carga el archivo Prolog si no está cargado.
        """
        if self._prolog is None:
            if not os.path.exists(self.prolog_file_path):
                raise FileNotFoundError(f"Archivo Prolog no encontrado: {self.prolog_file_path}")

            self._prolog = Prolog()
            self._prolog.consult(self.prolog_file_path)
            # Inicializar el sistema (carga datos de BD a Prolog)
            list(self._prolog.query("inicializar_sistema"))
            print(f"✓ Sistema Prolog inicializado desde {self.prolog_file_path}")

    def check_plant(self, plant: str, diagnostic: str) -> str:
        """
        Consulta el sistema Prolog para verificar si se necesita activar alertas.

        Args:
            plant: Nombre de la planta (tomate, maiz, uva, papa)
            diagnostic: Diagnóstico obtenido (ej: "late_blight", "healthy")

        Returns:
            Respuesta del sistema Prolog
        """
        try:
            self._initialize_prolog()

            # Realizar consulta
            query = f"check_planta('{plant}', '{diagnostic}', Respuesta)"
            results = list(self._prolog.query(query))

            if results:
                response = results[0]['Respuesta']
                print(f"🤖 Prolog response: {response}")
                return response
            else:
                return f"No se pudo procesar la consulta para {plant} con diagnóstico {diagnostic}"

        except Exception as e:
            error_msg = f"Error en consulta Prolog: {str(e)}"
            print(f"✗ {error_msg}")
            return error_msg

    def reload_system(self):
        """
        Recarga el sistema Prolog (útil si cambiaron los datos en BD).
        """
        try:
            if self._prolog:
                list(self._prolog.query("inicializar_sistema"))
                print("✓ Sistema Prolog recargado")
        except Exception as e:
            print(f"✗ Error al recargar Prolog: {str(e)}")
            raise

    def query_custom(self, query: str) -> list:
        """
        Ejecuta una consulta Prolog personalizada.

        Args:
            query: Consulta Prolog en formato string

        Returns:
            Lista de resultados
        """
        try:
            self._initialize_prolog()
            return list(self._prolog.query(query))
        except Exception as e:
            print(f"✗ Error en consulta personalizada: {str(e)}")
            raise
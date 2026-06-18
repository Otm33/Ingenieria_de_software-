import csv

from .base import BusinessError
from ..interfaces.service_interfaces import CargaUsuariosInterface
from ..repositorios_implementacion import UsuarioAutorizadoRepository


class CargaUsuariosService(CargaUsuariosInterface):
    def __init__(self, autorizados_repository=None):
        self.autorizados_repository = autorizados_repository or UsuarioAutorizadoRepository()
        self.emails_procesados = []

    def cargar_desde_archivo(self, archivo):
        if not archivo:
            raise BusinessError("No se recibio ningun archivo bajo los nombres 'archivo_csv' o 'archivo'.")

        data = archivo.read().decode("utf-8").splitlines()
        
        # Intentar formato nuevo con secciones separadas
        try:
            return self._cargar_formato_secciones(data)
        except BusinessError:
            # Si falla, intentar formato antiguo con columnas
            return self._cargar_formato_columnas(data)

    def _cargar_formato_secciones(self, data):
        creados = 0
        self.emails_procesados = []
        seccion_actual = None
        
        for linea in data:
            linea = linea.strip()
            if not linea:
                continue
            
            if linea == "email Usuarios":
                seccion_actual = "USUARIO"
                continue
            elif linea == "email Comercios":
                seccion_actual = "COMERCIO"
                continue
            
            if seccion_actual and linea:
                email = linea
                _, creado = self.autorizados_repository.guardar_email(email, seccion_actual)
                self.emails_procesados.append(f"{email} ({seccion_actual.lower()})")
                if creado:
                    creados += 1
        
        if not self.emails_procesados:
            raise BusinessError("No se encontraron emails en el archivo.")
        
        return {
            "mensaje": f"Lista procesada con exito. Se cargaron {creados} correos autorizados.",
            "emails_procesados": self.emails_procesados,
        }

    def _cargar_formato_columnas(self, data):
        reader = csv.DictReader(data)
        if not reader.fieldnames:
            raise BusinessError("El CSV debe tener las columnas 'email Usuarios' y 'email Comercios'.")

        creados = 0
        self.emails_procesados = []
        for row in reader:
            for columna, tipo in (("email Usuarios", "USUARIO"), ("email Comercios", "COMERCIO")):
                email = (row.get(columna) or "").strip()
                if not email:
                    continue

                _, creado = self.autorizados_repository.guardar_email(email, tipo)
                self.emails_procesados.append(f"{email} ({tipo.lower()})")
                if creado:
                    creados += 1

        return {
            "mensaje": f"Lista procesada con exito. Se cargaron {creados} correos autorizados.",
            "emails_procesados": self.emails_procesados,
        }

from comunidad.dto.request_models import RegistroUsuarioRequest
from comunidad.repositorios_interfaces import IUsuarioRepository
from comunidad.dominio.entidades import UsuarioDominio

class RegistroUsuarioController:
    """
    Controlador para la Historia de Usuario: Registro de Usuario.
    Recibe la interfaz del repositorio (Inversión de Dependencias).
    """
    def __init__(self, usuario_repository: IUsuarioRepository):
        self.repo = usuario_repository

    def ejecutar(self, request_data: RegistroUsuarioRequest) -> dict:
        # 1. Validación de DTO
        if not request_data.email or "@" not in request_data.email:
            raise ValueError("El correo electrónico no es válido.")
        if len(request_data.password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        
        # 2. Verificar si ya existe en la base de datos (usando repositorio)
        existente = self.repo.obtener_por_email(request_data.email)
        if existente:
            raise ValueError("El correo electrónico ya está registrado.")

        # 3. Construir la entidad de dominio (sin tocar base de datos en constructor)
        nuevo_usuario = UsuarioDominio(
            username=request_data.username,
            email=request_data.email,
            nombre_real=request_data.nombre_real,
            es_comercio=request_data.es_comercio
        )

        # 4. Llamar al repositorio para persistir la entidad
        usuario_guardado = self.repo.guardar(nuevo_usuario, password=request_data.password)

        # 5. Retornar los datos para la presentación
        return {
            "id": usuario_guardado.id,
            "username": usuario_guardado.username,
            "email": usuario_guardado.email,
            "es_comercio": usuario_guardado.es_comercio,
            "mensaje": "Usuario registrado exitosamente."
        }

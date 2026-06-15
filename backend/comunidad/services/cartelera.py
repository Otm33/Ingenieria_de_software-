from ..interfaces import CarteleraInterface
from ..repositories_legado import PublicacionRepository


class CarteleraService(CarteleraInterface):
    def __init__(self, publicacion_repository=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()

    def obtener_publicaciones(self, categoria=None, urgencias=None):
        return self.publicacion_repository.obtener_cartelera(categoria=categoria, urgencias=urgencias)

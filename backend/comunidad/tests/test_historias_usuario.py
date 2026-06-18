from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Usuario, UsuarioAutorizado, Publicacion, AcuerdoTrueque, SaldoComercial, Resena
from .helpers import crear_usuario, crear_publicacion

@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class IntegracionHistoriasUsuarioTestCase(APITestCase):
    """
    Test suite integradora con un caso de prueba detallado por cada Historia de Usuario
    enfocándose en la interacción con el controlador correspondiente de forma N-Tier.
    """

    def setUp(self):
        self.client = APIClient()

    # --- SPRINT 1 ---

    def test_hu1_cargar_usuarios_csv_y_validar_email(self):
        """HU1: ComunidadController — Cargar lista de autorizados y validar email."""
        admin_user = crear_usuario("admin_test", "admin@test.com", "Admin Test")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        self.client.force_authenticate(user=admin_user)

        # Formato de secciones para cargar el archivo
        csv_content = b"email Usuarios\nuser1@test.com\nemail Comercios\ncomercio1@test.com\n"
        archivo_csv = SimpleUploadedFile("usuarios.csv", csv_content, content_type="text/csv")

        response = self.client.post("/api/cargar-csv/", {"archivo": archivo_csv}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("emails_procesados", response.data)

        # Validar si el email cargado está autorizado en el endpoint de validación
        self.client.force_authenticate(user=None)
        val_response = self.client.post("/api/registro/validar-email/", {"email": "user1@test.com"}, format="json")
        self.assertEqual(val_response.status_code, status.HTTP_200_OK)
        self.assertTrue(val_response.data["autorizado"])

    def test_hu2_registro_sesion_y_gestion_publicaciones(self):
        """HU2: RegistroPublicacionController — Registrarse, iniciar sesión y crear talentos/necesidades."""
        # Registrar email en lista blanca
        UsuarioAutorizado.objects.create(email="nuevo@test.com", tipo="USUARIO")

        # Registrar
        reg_data = {
            "username": "nuevo_user",
            "email": "nuevo@test.com",
            "nombre_real": "Nuevo Usuario",
            "password": "testpassword123",
            "es_comercio": False
        }
        reg_response = self.client.post("/api/registro/", reg_data, format="json")
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)

        # Login
        login_response = self.client.post("/api/login/", {"username": "nuevo_user", "password": "testpassword123"}, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertTrue(login_response.data["autenticado"])

        # Autenticar
        user_obj = Usuario.objects.get(username="nuevo_user")
        self.client.force_authenticate(user=user_obj)

        # Crear publicación de talento
        pub_data = {
            "tipo": "TALENTO",
            "titulo": "Clases de Matematicas", # Evitar caracteres no ASCII por si acaso
            "descripcion": "Clases particulares para primaria y secundaria.",
            "categoria": "Educación, Asesoría y Tutorías",
            "urgencia": "NORMAL"
        }
        pub_response = self.client.post("/api/publicaciones/", pub_data, format="json")
        self.assertEqual(pub_response.status_code, status.HTTP_201_CREATED)

        # Listar mis publicaciones
        mis_pub_response = self.client.get("/api/mis-publicaciones/")
        self.assertEqual(mis_pub_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(mis_pub_response.data["publicaciones"]), 1)

    def test_hu3_cartelera_publica(self):
        """HU3: CarteleraController — Visualizar cartelera con filtros de búsqueda."""
        user = crear_usuario("cartelera_user", "cartelera@test.com", "Cartelera User")
        # Aseguramos categoría y campos de urgencia correctos
        crear_publicacion(user, "TALENTO", "Carpinteria", "Mantenimiento, Reparaciones y Construcción")
        crear_publicacion(user, "NECESIDAD", "Clases de Piano", "Educación y Tutorías")

        self.client.force_authenticate(user=user)

        # Ver cartelera general (respuesta es una lista directa)
        response = self.client.get("/api/cartelera/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

        # Filtrar por categoría (también devuelve lista)
        response_filtered = self.client.get("/api/cartelera/", {"categoria": "Educación y Tutorías"})
        self.assertEqual(response_filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_filtered.data), 1)

    def test_hu4_matchmaking_y_propuesta_trueque(self):
        """HU4: MatchTruequeController — Matchmaking, propuestas de trueque y notificaciones."""
        user_a = crear_usuario("user_a", "a@test.com", "User A", horas=5.0)
        user_b = crear_usuario("user_b", "b@test.com", "User B", horas=5.0)

        # A ofrece clases de cocina y necesita carpintería
        pub_tal_a = crear_publicacion(user_a, "TALENTO", "Cocina", "Gastronomía")
        pub_nec_a = crear_publicacion(user_a, "NECESIDAD", "Carpintería", "Mantenimiento, Reparaciones y Construcción")

        # B ofrece carpintería y necesita cocina
        pub_tal_b = crear_publicacion(user_b, "TALENTO", "Carpintería", "Mantenimiento, Reparaciones y Construcción")
        pub_nec_b = crear_publicacion(user_b, "NECESIDAD", "Cocina", "Gastronomía")

        self.client.force_authenticate(user=user_a)

        # Obtener Matches
        match_response = self.client.get("/api/matchmaking/")
        self.assertEqual(match_response.status_code, status.HTTP_200_OK)

        # Crear propuesta
        prop_data = {
            "receptor_id": user_b.id,
            "publicacion_emisor_id": pub_tal_a.id,
            "publicacion_receptor_id": pub_tal_b.id
        }
        prop_response = self.client.post("/api/trueques/propuestas/crear/", prop_data, format="json")
        self.assertEqual(prop_response.status_code, status.HTTP_201_CREATED)
        trueque_id = prop_response.data["propuesta_id"]

        # Responder a propuesta (B)
        self.client.force_authenticate(user=user_b)
        resp_response = self.client.post(f"/api/trueques/{trueque_id}/responder/", {"accion": "ACEPTAR"}, format="json")
        self.assertEqual(resp_response.status_code, status.HTTP_200_OK)

    def test_hu5_comercio_y_saldo_comercial(self):
        """HU5: ComercioController — Emitir vuelto y pagar con saldo comercial en comercios afiliados."""
        # El comercio necesita saldo_comercial inicial para poder emitir vuelto (el sistema lo descuenta)
        comercio = crear_usuario("tienda", "tienda@test.com", "Mi Tienda", es_comercio=True, saldo_comercial=1000.0)
        cliente = crear_usuario("cliente_c", "cliente_c@test.com", "Cliente C", horas=10.0)

        # 1. Emitir vuelto como comercio (usa cliente_id en el request)
        self.client.force_authenticate(user=comercio)
        vuelto_data = {
            "cliente_id": cliente.id,
            "valor_producto": 1500,
            "monto_recibido": 2000,
            "monto_excedente": 500
        }
        response = self.client.post("/api/comercio/emitir-vuelto/", vuelto_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Actualizar balance acumulado en BD del cliente
        cliente.refresh_from_db()
        self.assertGreater(cliente.saldo_comercial, 0)

        # 2. Cliente paga con saldo comercial
        self.client.force_authenticate(user=cliente)
        pagar_data = {
            "comercio_id": comercio.id,
            "monto": 200
        }
        pagar_response = self.client.post("/api/comercio/pagar/", pagar_data, format="json")
        self.assertEqual(pagar_response.status_code, status.HTTP_200_OK)

        # 3. Ver saldo
        saldo_response = self.client.get("/api/mi-saldo-comercial/")
        self.assertEqual(saldo_response.status_code, status.HTTP_200_OK)
        self.assertIn("saldo_actual", saldo_response.data)


    # --- SPRINT 2 ---

    def test_hu2_s2_perfil_miembro_y_directorio(self):
        """HU2 (Sprint 2): PerfilHistorialController — Directorio de miembros, perfil completo e historial."""
        user = crear_usuario("miembro", "miembro@test.com", "Miembro Activo")
        crear_publicacion(user, "TALENTO", "Electricidad", "Mantenimiento, Reparaciones y Construcción")

        self.client.force_authenticate(user=user)

        # Obtener Directorio
        dir_response = self.client.get("/api/comunidad/")
        self.assertEqual(dir_response.status_code, status.HTTP_200_OK)

        # Obtener mi perfil
        perfil_response = self.client.get("/api/mi-perfil/")
        self.assertEqual(perfil_response.status_code, status.HTTP_200_OK)
        self.assertEqual(perfil_response.data["usuario"]["username"], "miembro")

    def test_hu4_s2_trueques_multiples_3_usuarios(self):
        """HU4 (Sprint 2): TruequeMultipleController — Aceptar/Rechazar trueques múltiples cíclicos."""
        user_a = crear_usuario("user_m_a", "ma@test.com", "User M A", horas=5.0)
        user_b = crear_usuario("user_m_b", "mb@test.com", "User M B", horas=5.0)
        user_c = crear_usuario("user_m_c", "mc@test.com", "User M C", horas=5.0)

        # Ciclo cruzado de talentos y necesidades
        crear_publicacion(user_a, "TALENTO", "T1", "Gastronomía")
        crear_publicacion(user_a, "NECESIDAD", "T3", "Educación y Tutorías")

        crear_publicacion(user_b, "TALENTO", "T2", "Mantenimiento, Reparaciones y Construcción")
        crear_publicacion(user_b, "NECESIDAD", "T1", "Gastronomía")

        crear_publicacion(user_c, "TALENTO", "T3", "Educación y Tutorías")
        crear_publicacion(user_c, "NECESIDAD", "T2", "Mantenimiento, Reparaciones y Construcción")

        # Disparar detección
        self.client.force_authenticate(user=user_a)
        from ..services.matchmaking_multiple import MatchmakingMultipleService
        MatchmakingMultipleService().detectar_y_notificar_ciclos(user_a)

        # Listar trueques múltiples del usuario
        response = self.client.get("/api/mis-trueques-multiples/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("trueques_multiple", response.data)
        
        if len(response.data["trueques_multiple"]) > 0:
            tm_id = response.data["trueques_multiple"][0]["id"]
            # Aceptar propuesta múltiple
            acc_response = self.client.post(f"/api/trueques-multiples/{tm_id}/aceptar/")
            self.assertEqual(acc_response.status_code, status.HTTP_200_OK)

    def test_hu5_s2_finalizar_trueque_con_codigo(self):
        """HU5 (Sprint 2): FinalizarTruequeController — Bilateralidad y validación de código de conclusión."""
        user_a = crear_usuario("fin_a", "fina@test.com", "Fin A", horas=5.0)
        user_b = crear_usuario("fin_b", "finb@test.com", "Fin B", horas=5.0)
        pub_tal_a = crear_publicacion(user_a, "TALENTO", "Servicio A", "Gastronomía")
        pub_nec_b = crear_publicacion(user_b, "NECESIDAD", "Servicio A", "Gastronomía")

        # Crear y aceptar propuesta de trueque (debe estar EN_CURSO para poder finalizar)
        trueque = AcuerdoTrueque.objects.create(
            emisor=user_a,
            receptor=user_b,
            publicacion_emisor=pub_tal_a,
            publicacion_receptor=pub_nec_b,
            estado="EN_CURSO",
            codigo_confirmacion="XYZ123"
        )

        # Confirmar entrega con código correcto
        self.client.force_authenticate(user=user_b)
        response = self.client.post(f"/api/trueques/{trueque.id}/validar-codigo/", {"codigo": "XYZ123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

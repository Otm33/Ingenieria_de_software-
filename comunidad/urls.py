from django.urls import path

# Sprint 1 HU 1 — Comunidad y CSV
from .routers.hu_s1_hu1_comunidad_router import (
    CargarUsuariosCSVRouter,
    SetupAdminRouter,
    ValidarEmailRegistroRouter,
)

# Sprint 1 HU 2 — Registro, sesión y publicaciones
from .routers.hu_s1_hu2_registro_publicacion_router import (
    CrearPublicacionRouter,
    GestionPublicacionRouter,
    LoginRouter,
    LogoutRouter,
    MisPublicacionesRouter,
    RegistroRouter,
    SesionRouter,
)

# Sprint 1 HU 3 — Cartelera
from .routers.hu_s1_hu3_cartelera_router import CarteleraRouter

# Sprint 1 HU 4 — Match, propuestas, notificaciones y reseñas
from .routers.hu_s1_hu4_match_trueque_router import (
    CrearPropuestaRouter,
    CrearResenaRouter,
    MarcarLeidaRouter,
    MatchmakingRouter,
    NotificacionRouter,
    ResponderPropuestaRouter,
)

# Sprint 1 HU 5 — Comercio y saldo comercial
from .routers.hu_s1_hu5_comercio_router import (
    ClientesRouter,
    ComerciosRouter,
    EmitirVueltoRouter,
    MiSaldoComercialRouter,
    PagarConSaldoRouter,
)

# Sprint 2 HU 2 — Perfil e historial
from .routers.hu_s2_hu2_perfil_router import (
    ComunidadRouter,
    MiPerfilRouter,
    MisTruequesRouter,
    PerfilOtroUsuarioRouter,
)

# Sprint 2 HU 4 — Trueques múltiples
from .routers.hu_s2_hu4_trueque_multiple_router import (
    AceptarTruequeMultipleRouter,
    CrearResenaMultipleRouter,
    FinalizarTruequeMultipleRouter,
    MisTruequesMultiplesRouter,
    RechazarTruequeMultipleRouter,
    ValidarCodigoTruequeMultipleRouter,
)

# Sprint 2 HU 5 — Finalizar trueque con código
from .routers.hu_s2_hu5_finalizar_trueque_router import (
    FinalizarTruequeRouter,
    ValidarCodigoRouter,
)


urlpatterns = [
    # Sprint 1 HU 1 — Comunidad
    path("setup-admin/<str:username>/", SetupAdminRouter.as_view(), name="setup_admin_temp"),
    path("cargar-csv/", CargarUsuariosCSVRouter.as_view(), name="cargar_csv"),
    path("registro/validar-email/", ValidarEmailRegistroRouter.as_view(), name="validar_email_registro"),

    # Sprint 1 HU 2 — Registro, sesión y publicaciones
    path("sesion/", SesionRouter.as_view(), name="sesion_actual"),
    path("login/", LoginRouter.as_view(), name="login"),
    path("logout/", LogoutRouter.as_view(), name="logout"),
    path("registro/", RegistroRouter.as_view(), name="registro"),
    path("publicaciones/", CrearPublicacionRouter.as_view(), name="crear_publicacion"),
    path("publicaciones/<int:pk>/", GestionPublicacionRouter.as_view(), name="actualizar_publicacion"),
    path("mis-publicaciones/", MisPublicacionesRouter.as_view(), name="mis_publicaciones"),

    # Sprint 1 HU 3 — Cartelera
    path("cartelera/", CarteleraRouter.as_view(), name="cartelera"),

    # Sprint 1 HU 4 — Match, propuestas, notificaciones y reseñas
    path("matchmaking/", MatchmakingRouter.as_view(), name="matchmaking"),
    path("trueques/propuestas/crear/", CrearPropuestaRouter.as_view(), name="crear_propuesta"),
    path("trueques/<int:trueque_id>/responder/", ResponderPropuestaRouter.as_view(), name="responder_propuesta"),
    path("notificaciones/", NotificacionRouter.as_view(), name="notificaciones"),
    path("notificaciones/marcar-leida/", MarcarLeidaRouter.as_view(), name="marcar_leida"),
    path("resenas/", CrearResenaRouter.as_view(), name="registrar_resena"),

    # Sprint 1 HU 5 — Comercio
    path("comercio/emitir-vuelto/", EmitirVueltoRouter.as_view(), name="emitir_vuelto"),
    path("comercios/", ComerciosRouter.as_view(), name="catalogo_comercios"),
    path("clientes/", ClientesRouter.as_view(), name="catalogo_clientes"),
    path("comercio/pagar/", PagarConSaldoRouter.as_view(), name="pagar_con_saldo"),
    path("mi-saldo-comercial/", MiSaldoComercialRouter.as_view(), name="ver_saldo_comercial"),

    # Sprint 2 HU 2 — Perfil e historial
    path("comunidad/", ComunidadRouter.as_view(), name="directorio_comunidad"),
    path("perfil/<int:user_id>/", PerfilOtroUsuarioRouter.as_view(), name="ver_perfil_usuario"),
    path("mi-perfil/", MiPerfilRouter.as_view(), name="ver_mi_perfil"),
    path("mis-trueques/", MisTruequesRouter.as_view(), name="mis_trueques"),

    # Sprint 2 HU 4 — Trueques múltiples
    path("mis-trueques-multiples/", MisTruequesMultiplesRouter.as_view(), name="mis_trueques_multiples"),
    path("trueques-multiples/<int:trueque_multiple_id>/aceptar/", AceptarTruequeMultipleRouter.as_view(), name="aceptar_propuesta_multiple"),
    path("trueques-multiples/<int:trueque_multiple_id>/rechazar/", RechazarTruequeMultipleRouter.as_view(), name="rechazar_propuesta_multiple"),
    path("trueques-multiples/<int:trueque_multiple_id>/validar-codigo/", ValidarCodigoTruequeMultipleRouter.as_view(), name="validar_codigo_par_multiple"),
    path("trueques-multiples/<int:trueque_multiple_id>/finalizar-par/", FinalizarTruequeMultipleRouter.as_view(), name="finalizar_par_multiple"),
    path("resenas-multiples/", CrearResenaMultipleRouter.as_view(), name="registrar_resena_multiple"),

    # Sprint 2 HU 5 — Finalizar trueque con código
    path("trueques/<int:trueque_id>/finalizar/", FinalizarTruequeRouter.as_view(), name="finalizar_trueque"),
    path("trueques/<int:trueque_id>/validar-codigo/", ValidarCodigoRouter.as_view(), name="validar_codigo"),
]

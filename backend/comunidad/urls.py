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

# Sprint 2 HU1 — Impacto Social
from .routers.hu_s2_hu1_impacto_social_router import (
    ImpactoSocialSolicitudesRouter,
    MisSolicitudesImpactoSocialRouter,
    ActivarNecesidadImpactoSocialRouter,
    MisDonacionesImpactoSocialRouter,
    DonarCausaImpactoSocialRouter,
    DonarFondoImpactoSocialRouter,
    AdminSolicitudesPendientesImpactoSocialRouter,
    AdminAprobarSolicitudImpactoSocialRouter,
    AdminRechazarSolicitudImpactoSocialRouter,
    AdminUsuariosImpactoSocialRouter,
    AdminEstadoSocialImpactoSocialRouter,
    AdminFondoImpactoSocialRouter,
    AdminAsignarFondoImpactoSocialRouter,
)

# Sprint 2 HU3 — Panel de Administracion
from .routers.hu_s2_hu3_admin_panel_router import (
    AdminPanelDashboardRouter,
    AdminPanelUsuariosRouter,
    AdminPanelToggleUsuarioRouter,
    AdminPanelRolUsuarioRouter,
    AdminPanelEliminarUsuarioRouter,
    AdminPanelEditarUsuarioRouter,
    AdminPanelPublicacionesRouter,
    AdminPanelCrearPublicacionRouter,
    AdminPanelModerarPublicacionRouter,
    AdminPanelEliminarPublicacionRouter,
    AdminPanelEditarPublicacionRouter,
    AdminPanelTruequesRouter,
    AdminPanelEstadoTruequeRouter,
    AdminPanelEliminarTruequeRouter,
    AdminPanelTruequesMultiplesRouter,
    AdminPanelEstadoTruequeMultipleRouter,
    AdminPanelEliminarTruequeMultipleRouter,
    AdminPanelResenasRouter,
    AdminPanelEliminarResenaRouter,
    AdminPanelResenasMultiplesRouter,
    AdminPanelEliminarResenaMultipleRouter,
    AdminPanelSaldosRouter,
)

# Tactica "Autorizar Actores" — Metricas de seguridad
from .routers.seguridad_metricas_router import (
    MetricasAutorizacionRouter,
    HistorialAutorizacionRouter,
    LimpiarAuditoriaRouter,
)

urlpatterns = [
    # Sprint 1 HU 1 — Comunidad
    path("setup-admin/<str:username>/", SetupAdminRouter.as_view(), name="setup_admin_temp"),
    path("cargar-csv/", CargarUsuariosCSVRouter.as_view(), name="cargar_csv"),
    path("registro/validar-email/", ValidarEmailRegistroRouter.as_view(), name="validar_email_registro"),

    # Sprint 1 HU 2 — Registro, sesion y publicaciones
    path("sesion/", SesionRouter.as_view(), name="sesion_actual"),
    path("login/", LoginRouter.as_view(), name="login"),
    path("logout/", LogoutRouter.as_view(), name="logout"),
    path("registro/", RegistroRouter.as_view(), name="registro"),
    path("publicaciones/", CrearPublicacionRouter.as_view(), name="crear_publicacion"),
    path("publicaciones/<int:pk>/", GestionPublicacionRouter.as_view(), name="actualizar_publicacion"),
    path("mis-publicaciones/", MisPublicacionesRouter.as_view(), name="mis_publicaciones"),

    # Sprint 1 HU 3 — Cartelera
    path("cartelera/", CarteleraRouter.as_view(), name="cartelera"),

    # Sprint 1 HU 4 — Match, propuestas, notificaciones y resenas
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

    # Sprint 2 HU 4 — Trueques multiples
    path("mis-trueques-multiples/", MisTruequesMultiplesRouter.as_view(), name="mis_trueques_multiples"),
    path("trueques-multiples/<int:trueque_multiple_id>/aceptar/", AceptarTruequeMultipleRouter.as_view(), name="aceptar_propuesta_multiple"),
    path("trueques-multiples/<int:trueque_multiple_id>/rechazar/", RechazarTruequeMultipleRouter.as_view(), name="rechazar_propuesta_multiple"),
    path("trueques-multiples/<int:trueque_multiple_id>/validar-codigo/", ValidarCodigoTruequeMultipleRouter.as_view(), name="validar_codigo_par_multiple"),
    path("trueques-multiples/<int:trueque_multiple_id>/finalizar-par/", FinalizarTruequeMultipleRouter.as_view(), name="finalizar_par_multiple"),
    path("resenas-multiples/", CrearResenaMultipleRouter.as_view(), name="registrar_resena_multiple"),

    # Sprint 2 HU 5 — Finalizar trueque con codigo
    path("trueques/<int:trueque_id>/finalizar/", FinalizarTruequeRouter.as_view(), name="finalizar_trueque"),
    path("trueques/<int:trueque_id>/validar-codigo/", ValidarCodigoRouter.as_view(), name="validar_codigo"),

    # Sprint 2 HU1 — Impacto Social
    path("impacto-social/solicitudes/", ImpactoSocialSolicitudesRouter.as_view(), name="impacto_social_solicitudes"),
    path("impacto-social/mis-solicitudes/", MisSolicitudesImpactoSocialRouter.as_view(), name="impacto_social_mis_solicitudes"),
    path("impacto-social/solicitudes/<int:solicitud_id>/activar-necesidad/", ActivarNecesidadImpactoSocialRouter.as_view(), name="impacto_social_activar_necesidad"),
    path("impacto-social/mis-donaciones/", MisDonacionesImpactoSocialRouter.as_view(), name="impacto_social_mis_donaciones"),
    path("impacto-social/donar/", DonarCausaImpactoSocialRouter.as_view(), name="impacto_social_donar"),
    path("impacto-social/donar-fondo/", DonarFondoImpactoSocialRouter.as_view(), name="impacto_social_donar_fondo"),
    path("admin/impacto-social/solicitudes-pendientes/", AdminSolicitudesPendientesImpactoSocialRouter.as_view(), name="admin_impacto_social_pendientes"),
    path("admin/impacto-social/solicitudes/<int:solicitud_id>/aprobar/", AdminAprobarSolicitudImpactoSocialRouter.as_view(), name="admin_impacto_social_aprobar"),
    path("admin/impacto-social/solicitudes/<int:solicitud_id>/rechazar/", AdminRechazarSolicitudImpactoSocialRouter.as_view(), name="admin_impacto_social_rechazar"),
    path("admin/impacto-social/usuarios/", AdminUsuariosImpactoSocialRouter.as_view(), name="admin_impacto_social_usuarios"),
    path("admin/impacto-social/usuarios/<int:usuario_id>/estado-social/", AdminEstadoSocialImpactoSocialRouter.as_view(), name="admin_impacto_social_estado_social"),
    path("admin/impacto-social/fondo/", AdminFondoImpactoSocialRouter.as_view(), name="admin_impacto_social_fondo"),
    path("admin/impacto-social/fondo/asignar/", AdminAsignarFondoImpactoSocialRouter.as_view(), name="admin_impacto_social_asignar_fondo"),

    # Sprint 2 HU3 — Panel de Administracion
    path("admin/panel/dashboard/", AdminPanelDashboardRouter.as_view(), name="admin_panel_dashboard"),
    path("admin/panel/usuarios/", AdminPanelUsuariosRouter.as_view(), name="admin_panel_usuarios"),
    path("admin/panel/usuarios/<int:usuario_id>/toggle/", AdminPanelToggleUsuarioRouter.as_view(), name="admin_panel_toggle_usuario"),
    path("admin/panel/usuarios/<int:usuario_id>/rol/", AdminPanelRolUsuarioRouter.as_view(), name="admin_panel_rol_usuario"),
    path("admin/panel/usuarios/<int:usuario_id>/editar/", AdminPanelEditarUsuarioRouter.as_view(), name="admin_panel_editar_usuario"),
    path("admin/panel/usuarios/<int:usuario_id>/", AdminPanelEliminarUsuarioRouter.as_view(), name="admin_panel_eliminar_usuario"),
    path("admin/panel/publicaciones/", AdminPanelPublicacionesRouter.as_view(), name="admin_panel_publicaciones"),
    path("admin/panel/publicaciones/crear/", AdminPanelCrearPublicacionRouter.as_view(), name="admin_panel_crear_publicacion"),
    path("admin/panel/publicaciones/<int:publicacion_id>/moderar/", AdminPanelModerarPublicacionRouter.as_view(), name="admin_panel_moderar_publicacion"),
    path("admin/panel/publicaciones/<int:publicacion_id>/editar/", AdminPanelEditarPublicacionRouter.as_view(), name="admin_panel_editar_publicacion"),
    path("admin/panel/publicaciones/<int:publicacion_id>/", AdminPanelEliminarPublicacionRouter.as_view(), name="admin_panel_eliminar_publicacion"),
    path("admin/panel/trueques/", AdminPanelTruequesRouter.as_view(), name="admin_panel_trueques"),
    path("admin/panel/trueques/<int:trueque_id>/estado/", AdminPanelEstadoTruequeRouter.as_view(), name="admin_panel_estado_trueque"),
    path("admin/panel/trueques/<int:trueque_id>/", AdminPanelEliminarTruequeRouter.as_view(), name="admin_panel_eliminar_trueque"),
    path("admin/panel/trueques-multiples/", AdminPanelTruequesMultiplesRouter.as_view(), name="admin_panel_trueques_multiples"),
    path("admin/panel/trueques-multiples/<int:trueque_id>/estado/", AdminPanelEstadoTruequeMultipleRouter.as_view(), name="admin_panel_estado_trueque_multiple"),
    path("admin/panel/trueques-multiples/<int:trueque_id>/", AdminPanelEliminarTruequeMultipleRouter.as_view(), name="admin_panel_eliminar_trueque_multiple"),
    path("admin/panel/resenas/", AdminPanelResenasRouter.as_view(), name="admin_panel_resenas"),
    path("admin/panel/resenas/<int:resena_id>/", AdminPanelEliminarResenaRouter.as_view(), name="admin_panel_eliminar_resena"),
    path("admin/panel/resenas-multiples/", AdminPanelResenasMultiplesRouter.as_view(), name="admin_panel_resenas_multiples"),
    path("admin/panel/resenas-multiples/<int:resena_id>/", AdminPanelEliminarResenaMultipleRouter.as_view(), name="admin_panel_eliminar_resena_multiple"),
    path("admin/panel/saldos/", AdminPanelSaldosRouter.as_view(), name="admin_panel_saldos"),

    # Tactica "Autorizar Actores" (Bass, Clements & Kazman, 2023)
    # Endpoints para medir la metrica de efectividad de autorizacion
    path("seguridad/metricas-autorizacion/", MetricasAutorizacionRouter.as_view(), name="metricas_autorizacion"),
    path("seguridad/historial-autorizacion/", HistorialAutorizacionRouter.as_view(), name="historial_autorizacion"),
    path("seguridad/limpiar-auditoria/", LimpiarAuditoriaRouter.as_view(), name="limpiar_auditoria"),
]

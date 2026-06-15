import csv
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny 
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import UsuarioAutorizado, Usuario, Publicacion, AcuerdoTrueque, Resena, SaldoComercial
from .serializers import PublicacionSerializer, UsuarioSerializer, AcuerdoTruequeSerializer
from decimal import Decimal

class CargarUsuariosCSVView(APIView):
    # Usamos AllowAny temporalmente para facilitar las pruebas del Sprint 1 desde el puerto 5173
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        # 1. Intentamos leer el archivo usando ambos nombres posibles por seguridad
        archivo = request.FILES.get('archivo_csv') or request.FILES.get('archivo')
        
        if not archivo:
            return Response(
                {"error": "No se recibió ningún archivo bajo los nombres 'archivo_csv' o 'archivo'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2. Leer y decodificar el archivo CSV de forma segura
            data = archivo.read().decode('utf-8').splitlines()
            reader = csv.reader(data)
            
            # Omitir la fila de la cabecera (en nuestro caso, la palabra 'email')
            header = next(reader, None)
            
            emails_creados = 0
            for row in reader:
                if row:  # Asegurar que la línea no esté vacía
                    email = row[0].strip()
                    if email:
                        # get_or_create evita duplicados si subes el CSV más de una vez
                        UsuarioAutorizado.objects.get_or_create(email=email)
                        emails_creados += 1

            return Response(
                {"mensaje": f"Lista procesada con éxito. Se cargaron {emails_creados} correos autorizados."}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Si algo falla, imprimirá el error real en tu consola de Django
            print("ERROR INTERNO EN CARGA CSV:", str(e))
            return Response(
                {"error": f"Error interno al procesar el archivo: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class RegistroUsuarioView(APIView):
    """HU2: Registro validando contra la lista blanca del CSV."""
    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        nombre_real = request.data.get('nombre_real')

        if not UsuarioAutorizado.objects.filter(email=email).exists():
            return Response({"error": "Usuario no autorizado para esta comunidad"}, status=status.HTTP_403_FORBIDDEN)

        if Usuario.objects.filter(username=username).exists():
            return Response({"error": "El username ya está en uso."}, status=status.HTTP_400_BAD_REQUEST)

        user = Usuario.objects.create_user(
            username=username, email=email, password=password, nombre_real=nombre_real
        )
        return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)

class CarteleraFeedView(generics.ListAPIView):
    """HU3: Cartelera principal con ordenamiento por estrellas y priorización de urgencias."""
    serializer_class = PublicacionSerializer

    def get_queryset(self):
        queryset = Publicacion.objects.filter(esta_activa=True)
        categoria = self.request.query_params.get('categoria')
        urgencia = self.request.query_params.get('urgencia')

        if categoria:
            queryset = queryset.filter(categoria=categoria)
        if urgencia:
            queryset = queryset.filter(urgencia=urgencia)

        # Regla de Negocio: Urgencias críticas/altas primero.
        # Usuarios con menos de 3 estrellas van estrictamente al fondo.
        queryset = queryset.annotate(
            prioridad_urgencia=Case(
                When(urgencia='CRITICA', then=Value(3)),
                When(urgencia='ALTA', then=Value(2)),
                When(urgencia='NORMAL', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            prioridad_estrellas=Case(
                When(usuario__promedio_estrellas__lt=3.0, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        
        queryset = queryset.order_by('-prioridad_estrellas', '-prioridad_urgencia', '-id')
        return queryset

# Reemplazar la actual en comunidad/views.py

class FinalizarTruequeView(APIView):
    """HU4: Cierre transaccional confirmando por ambas partes."""
    permission_classes = [IsAuthenticated]

    def post(self, request, trueque_id):
        with transaction.atomic():
            trueque = AcuerdoTrueque.objects.select_for_update().get(id=trueque_id)
            
            # Registrar quién está confirmando
            if request.user == trueque.emisor:
                trueque.emisor_confirmado = True
            elif request.user == trueque.receptor:
                trueque.receptor_confirmado = True
            else:
                return Response({"error": "No eres parte de este trueque."}, status=status.HTTP_403_FORBIDDEN)
            
            trueque.save()

            # Solo transferir horas si AMBAS partes confirmaron
            if trueque.emisor_confirmado and trueque.receptor_confirmado:
                emisor = trueque.emisor
                receptor = trueque.receptor

                if emisor.horas_de_vida - 1.0 < -10.0:
                    return Response({"error": "Límite de balance negativo excedido (-10)."}, status=status.HTTP_400_BAD_REQUEST)

                emisor.horas_de_vida -= 1.0
                receptor.horas_de_vida += 1.0
                
                emisor.save()
                receptor.save()
                
                trueque.estado = 'FINALIZADO'
                trueque.save()
                
                return Response({"message": "Trueque finalizado. Saldos actualizados. Modal de reseña habilitado."})
            
            return Response({"message": "Confirmación registrada. A la espera de la otra parte."})


class RegistrarResenaView(APIView):
    """HU4: Registro de reseña y recalculo automático de reputación."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        trueque_id = request.data.get('trueque_id')
        estrellas = int(request.data.get('estrellas'))
        comentario = request.data.get('comentario')

        trueque = AcuerdoTrueque.objects.get(id=trueque_id)
        calificado = trueque.receptor if request.user == trueque.emisor else trueque.emisor

        # Guardar reseña
        Resena.objects.create(
            trueque=trueque, calificador=request.user, calificado=calificado, estrellas=estrellas, comentario=comentario
        )

        # Recalcular promedio de estrellas del usuario calificado
        resenas = Resena.objects.filter(calificado=calificado)
        total_estrellas = sum([r.estrellas for r in resenas])
        calificado.promedio_estrellas = total_estrellas / resenas.count()
        calificado.save()

        return Response({"message": "Reseña registrada y promedio actualizado."})


class EmitirVueltoComercialView(APIView):
    """HU5: Registro contable independiente de vuelto para red comercial."""
    permission_classes = [IsAuthenticated] # <--- Volver a proteger

    def post(self, request):
        # Volvemos a usar request.user porque el Token identificará al comercio logueado
        if not request.user.es_comercio:
            return Response({"error": "Solo comercios pueden emitir saldos comerciales."}, status=403)

        cliente_id = request.data.get('cliente_id')
        monto_str = request.data.get('monto_excedente')
        
        if not cliente_id or not monto_str:
            return Response({"error": "Faltan datos."}, status=400)

        try:
            monto = Decimal(str(monto_str)) # Mantén la conversión a Decimal que pusimos para evitar errores de tipo
            with transaction.atomic():
                cliente = Usuario.objects.select_for_update().get(id=cliente_id)
                cliente.saldo_comercial += monto
                cliente.save()

                SaldoComercial.objects.create(
                    comercio=request.user, # <--- Volver a request.user
                    cliente=cliente, 
                    monto_excedente=monto,
                    tipo_movimiento='EMISION'
                )
            return Response({"message": "Saldo a favor comercial emitido correctamente (Inalterable en horas de vida)."})
        except Usuario.DoesNotExist:
            return Response({"error": "El cliente especificado no existe."}, status=404)



# Añadir o modificar en comunidad/models.py




# Añadir en comunidad/views.py

class MatchmakingView(APIView):
    """HU4: Emparejamiento automático (Match) entre oferta y demanda."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario_actual = request.user
        
        # Suponiendo que en tu modelo 'Publicacion' tienes campos 'tipo' ('TALENTO' o 'NECESIDAD')
        mis_necesidades = Publicacion.objects.filter(usuario=usuario_actual, tipo='NECESIDAD', esta_activa=True).values_list('categoria', flat=True)
        mis_talentos = Publicacion.objects.filter(usuario=usuario_actual, tipo='TALENTO', esta_activa=True).values_list('categoria', flat=True)

        # Buscar usuarios que OFRECEN mis necesidades Y NECESITAN mis talentos
        matches = Usuario.objects.filter(
            publicaciones__tipo='TALENTO', publicaciones__categoria__in=mis_necesidades, publicaciones__esta_activa=True
        ).filter(
            publicaciones__tipo='NECESIDAD', publicaciones__categoria__in=mis_talentos, publicaciones__esta_activa=True
        ).exclude(id=usuario_actual.id).distinct()

        serializer = UsuarioSerializer(matches, many=True)
        return Response({"matches": serializer.data, "mensaje": "Se encontraron coincidencias (Match)."}, status=status.HTTP_200_OK)


# Añadir en comunidad/views.py

class CrearPropuestaView(APIView):
    """HU4: Enviar propuesta de intercambio."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        receptor_id = request.data.get('receptor_id')
        receptor = Usuario.objects.get(id=receptor_id)
        
        propuesta = AcuerdoTrueque.objects.create(
            emisor=request.user,
            receptor=receptor,
            estado='PENDIENTE'
        )
        return Response({"message": "Propuesta enviada con éxito.", "propuesta_id": propuesta.id}, status=status.HTTP_201_CREATED)

class ResponderPropuestaView(APIView):
    """HU4: Aceptar o Rechazar propuestas de intercambio."""
    permission_classes = [IsAuthenticated]

    def post(self, request, trueque_id):
        accion = request.data.get('accion') # 'ACEPTAR' o 'RECHAZAR'
        trueque = AcuerdoTrueque.objects.get(id=trueque_id, receptor=request.user)

        if accion == 'ACEPTAR':
            trueque.estado = 'ACEPTADO'
            trueque.save()
            return Response({"message": "Propuesta aceptada. Intercambio en curso."})
        elif accion == 'RECHAZAR':
            trueque.estado = 'RECHAZADO'
            trueque.save()
            return Response({"message": "Propuesta rechazada."})
        return Response({"error": "Acción inválida."}, status=status.HTTP_400_BAD_REQUEST)


# 2. NUEVO: Vista para el Catálogo de Comercios (Escenario 1)
class CatalogoComerciosView(generics.ListAPIView):
    """HU5: Buscador de comercios afiliados a la red."""
    permission_classes = [IsAuthenticated]
    serializer_class = UsuarioSerializer # Utiliza el que ya tienes

    def get_queryset(self):
        # Retorna solo los usuarios validados que son comercios
        return Usuario.objects.filter(es_comercio=True, is_active=True)

# 3. NUEVO: Vista para Pagar con Saldo en Otro Comercio (Escenario 3)

class PagarConSaldoView(APIView):
    permission_classes = [IsAuthenticated] # <--- Volver a proteger

    def post(self, request):
        comercio_id = request.data.get('comercio_id')
        monto_str = request.data.get('monto')

        if not comercio_id or not monto_str:
            return Response({"error": "Faltan datos."}, status=400)

        try:
            monto = Decimal(str(monto_str)) # Mantén el Decimal
            with transaction.atomic():
                # El cliente ahora vuelve a ser request.user (el usuario logueado con su Token)
                cliente = Usuario.objects.select_for_update().get(id=request.user.id)
                comercio = Usuario.objects.get(id=comercio_id)

                if not comercio.es_comercio:
                    return Response({"error": "El usuario de destino no es un comercio."}, status=400)

                if cliente.saldo_comercial < monto:
                    return Response({"error": "Saldo comercial insuficiente para realizar el pago."}, status=400)

                cliente.saldo_comercial -= monto
                cliente.save()

                SaldoComercial.objects.create(
                    comercio=comercio,
                    cliente=cliente, # <--- request.user
                    monto_excedente=monto,
                    tipo_movimiento='PAGO'
                )
            return Response({"message": "Pago procesado con éxito utilizando saldo comercial."})
        except Usuario.DoesNotExist:
            return Response({"error": "Comercio no encontrado."}, status=404)

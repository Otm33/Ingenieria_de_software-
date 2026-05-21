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
        ).order_index = queryset.order_by('-prioridad_estrellas', '-prioridad_urgencia', '-id')
        
        return queryset

class FinalizarTruequeView(APIView):
    """HU4: Cierre transaccional atómico de intercambio y actualización de saldos."""
    permission_classes = [IsAuthenticated]

    def post(self, request, trueque_id):
        with transaction.atomic():
            # select_for_update bloquea las filas en PostgreSQL para evitar condiciones de carrera (Requisito 2.4.2)
            trueque = AcuerdoTrueque.objects.select_for_update().get(id=trueque_id)
            
            emisor = trueque.emisor
            receptor = trueque.receptor

            if emisor.horas_de_vida - 1.0 < -10.0:
                return Response({"error": f"El usuario {emisor.username} excede el límite de balance negativo permitido (-10)."}, status=status.HTTP_400_BAD_REQUEST)

            # Transferencia de 1 Hora de Vida
            emisor.horas_de_vida -= 1.0
            receptor.horas_de_vida += 1.0
            
            emisor.save()
            receptor.save()
            
            trueque.estado = 'FINALIZADO'
            trueque.save()
            
            return Response({"message": "Trueque finalizado. Saldos actualizados de forma segura."})

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.es_comercio:
            return Response({"error": "Solo comercios pueden emitir saldos comerciales."}, status=403)

        cliente_id = request.data.get('cliente_id')
        monto = request.data.get('monto_excedente')
        cliente = Usuario.objects.get(id=cliente_id)

        SaldoComercial.objects.create(comercio=request.user, cliente=cliente, monto_excedente=monto)
        return Response({"message": "Saldo a favor comercial emitido correctamente (Inalterable en horas de vida)."})

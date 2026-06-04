from rest_framework import serializers
from .models import Usuario, Publicacion, AcuerdoTrueque, Resena, SaldoComercial

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        # CAMBIO AUTH: la vista usa is_staff/is_superuser para mostrar opciones solo a admins.
        fields = ['id', 'username', 'email', 'nombre_real', 'horas_de_vida', 'promedio_estrellas', 'es_comercio', 'is_staff', 'is_superuser']

class PublicacionSerializer(serializers.ModelSerializer):
    usuario_nombre_real = serializers.CharField(source='usuario.nombre_real', read_only=True)
    usuario_estrellas = serializers.FloatField(source='usuario.promedio_estrellas', read_only=True)

    class Meta:
        model = Publicacion
        fields = ['id', 'usuario', 'usuario_nombre_real', 'usuario_estrellas', 'tipo', 'titulo', 'descripcion', 'categoria', 'urgencia', 'esta_activa']

class AcuerdoTruequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcuerdoTrueque
        fields = '__all__'

class ResenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resena
        fields = ['id', 'trueque', 'calificador', 'calificado', 'estrellas', 'comentario']

class SaldoComercialSerializer(serializers.ModelSerializer):
    comercio_nombre = serializers.CharField(source='comercio.nombre_real', read_only=True)
    comercio_email = serializers.EmailField(source='comercio.email', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_real', read_only=True)
    cliente_email = serializers.EmailField(source='cliente.email', read_only=True)

    class Meta:
        model = SaldoComercial
        fields = ['id', 'comercio', 'comercio_nombre', 'comercio_email', 
                  'cliente', 'cliente_nombre', 'cliente_email', 
                  'monto_excedente', 'tipo_movimiento', 'fecha']

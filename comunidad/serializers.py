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

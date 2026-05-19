import csv
import io
import uuid
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import MiembroComunidad, CuentaSaldo


class ImportarMiembroComunidadSerializer(serializers.Serializer):
    """
    Importa miembros autorizados desde un CSV con columnas: nombre, email
    Crea un User de Django + MiembroComunidad (PENDIENTE) + CuentaSaldo.
    El miembro completará su cédula y contraseña en el registro real.
    """
    archivo = serializers.FileField()

    COLUMNAS_REQUERIDAS = {'nombre', 'email'}

    def validate_archivo(self, archivo):
        if not archivo.name.endswith('.csv'):
            raise serializers.ValidationError("El archivo debe ser un .csv")

        try:
            contenido = archivo.read().decode('utf-8')
        except UnicodeDecodeError:
            raise serializers.ValidationError("El archivo debe estar en UTF-8.")

        lector = csv.DictReader(io.StringIO(contenido))

        columnas = set(c.strip().lower() for c in (lector.fieldnames or []))
        faltantes = self.COLUMNAS_REQUERIDAS - columnas
        if faltantes:
            raise serializers.ValidationError(
                f"Faltan columnas requeridas: {faltantes}"
            )

        self._filas = list(lector)
        if not self._filas:
            raise serializers.ValidationError("El CSV no tiene filas de datos.")

        return archivo

    def create(self, validated_data):
        exitosos = []
        errores = []

        for i, fila in enumerate(self._filas, start=2):
            nombre = fila.get('nombre', '').strip()
            correo = fila.get('email', '').strip().lower()

            try:
                # Validaciones básicas
                if not nombre or not correo:
                    raise ValueError("Nombre o email vacío.")
                validate_email(correo)

                if MiembroComunidad.objects.filter(correo=correo).exists():
                    raise ValueError(f"El email '{correo}' ya está autorizado.")
                if User.objects.filter(email=correo).exists():
                    raise ValueError(f"Ya existe un usuario con email '{correo}'.")

                # Creamos todo en una transacción atómica
                with transaction.atomic():
                    # 1) User de Django (sin contraseña usable hasta que se registre)
                    user = User.objects.create_user(
                        username=correo,
                        email=correo,
                        first_name=nombre[:30],
                    )
                    user.set_unusable_password()
                    user.save()

                    # 2) Cédula temporal única (la actualizará al registrarse)
                    cedula_temp = f"TMP-{uuid.uuid4().hex[:12]}"

                    # 3) MiembroComunidad en estado PENDIENTE
                    miembro = MiembroComunidad.objects.create(
                        usuario=user,
                        nombre=nombre,
                        correo=correo,
                        cedula=cedula_temp,
                        estado=MiembroComunidad.Estado.PENDIENTE,
                    )

                    # 4) CuentaSaldo asociada (con saldo inicial de la config)
                    cuenta = CuentaSaldo.objects.create(miembro=miembro)
                    cuenta.inicializar_saldos()

                exitosos.append({
                    'nombre': nombre,
                    'correo': correo,
                    'cedula_temporal': cedula_temp,
                })

            except (ValueError, DjangoValidationError) as e:
                msg = '; '.join(e.messages) if isinstance(e, DjangoValidationError) else str(e)
                errores.append({'fila': i, 'error': msg})
            except Exception as e:
                errores.append({'fila': i, 'error': f"Error inesperado: {str(e)}"})

        return {
            'total': len(self._filas),
            'autorizados': len(exitosos),
            'fallidos': len(errores),
            'miembros_autorizados': exitosos,
            'errores': errores,
        }
    
class VerificarAutorizacionSerializer(serializers.Serializer):
    """
    Escenario 2 de HU1: verifica si un correo está autorizado
    para registrarse en la comunidad.
    """
    correo = serializers.EmailField()

    def validate_correo(self, correo):
        correo = correo.strip().lower()
        try:
            miembro = MiembroComunidad.objects.get(correo=correo)
        except MiembroComunidad.DoesNotExist:
            raise serializers.ValidationError(
                "Usuario no autorizado para esta comunidad"
            )

        if miembro.estado != MiembroComunidad.Estado.PENDIENTE:
            raise serializers.ValidationError(
                "Este correo ya fue registrado o no está disponible"
            )

        self.context['miembro'] = miembro
        return correo

    def to_representation(self, instance):
        miembro = self.context.get('miembro')
        return {
            'autorizado': True,
            'mensaje': 'Usuario autorizado, puede continuar el registro',
            'nombre': miembro.nombre,
            'correo': miembro.correo,
        }
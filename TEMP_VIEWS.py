class ValidarCodigoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request, trueque_id):
        try:
            codigo = request.data.get("codigo")
            if not codigo:
                return Response(
                    {"error": "Falta el código de confirmación"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            resultado = self.servicio.validar_codigo_finalizacion(request.user, trueque_id, codigo)
            trueque = AcuerdoTruequeRepository().obtener_por_participante(trueque_id, request.user)
            
            return Response({
                "message": resultado.get("mensaje", ""),
                "estado": trueque.estado,
                "saldo_transferido": resultado.get("saldo_transferido", False),
                "impacto_horas": resultado.get("impacto_horas", 0),
                "habilitar_resena": resultado.get("habilitar_resena", False),
            })
        except BusinessError as error:
            return manejar_error(error)
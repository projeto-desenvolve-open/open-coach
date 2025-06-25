from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from authentication.serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserRecoverySerializer,
    OtpVerifySerializer,
    ResetPasswordSerializer
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()


class UserRegisterViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar novos usuários e atribuir grupo 'user'
    """
    serializer_class = UserRegisterSerializer
    queryset = User.objects.all()
    http_method_names = ['post']


class UserLoginViewSet(viewsets.ViewSet):
    """
    ViewSet para login de usuários
    """
    serializer_class = UserLoginSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRecoveryViewSet(viewsets.ViewSet):
    """
    ViewSet para recuperar senha (envia OTP por e-mail)
    """
    serializer_class = UserRecoverySerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Código OTP enviado para o e-mail."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OtpVerifyViewSet(viewsets.ViewSet):
    """
    ViewSet para validar código OTP
    """
    serializer_class = OtpVerifySerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordViewSet(viewsets.ViewSet):
    serializer_class = ResetPasswordSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Senha redefinida com sucesso."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBlockViewSet(viewsets.ModelViewSet):
    """
    ViewSet para desativar usuários autenticados (via username)
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    @swagger_auto_schema(
        operation_description="Bloqueia um usuário pelo username",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username"],
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING, description="Username do usuário a ser bloqueado"),
            },
        ),
        responses={200: "Usuário bloqueado com sucesso", 404: "Usuário não encontrado"},
    )
    def create(self, request, *args, **kwargs):
        username = request.data.get("username")

        if not username:
            return Response({"error": "O campo 'username' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
            user.is_active = False
            user.save()
            return Response({"message": f"Usuário {username} bloqueado com sucesso."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)

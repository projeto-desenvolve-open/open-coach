from rest_framework import viewsets, permissions, status, serializers
from services.models.access_control import UserServiceAccess
from services.serializers.access_control_serializer import UserServiceAccessSerializer
from services.permissions.is_staff_or_admin import IsStaffOrAdmin
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class UserServiceAccessViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar o acesso dos usuários aos módulos do sistema.

    - Admin e Staff: acesso completo
    - Usuário comum: vê apenas seu próprio acesso
    - Superuser: tem acesso total fixo e não pode ser modificado
    """
    queryset = UserServiceAccess.objects.all()
    serializer_class = UserServiceAccessSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]

    def get_queryset(self):
        user = self.request.user

        # Evita erro para usuários anônimos (Swagger e testes não autenticados)
        if not user or not user.is_authenticated:
            return UserServiceAccess.objects.none()

        if user.is_superuser:
            return UserServiceAccess.objects.filter(user=user)

        if user.groups.filter(name__in=["admin", "staff"]).exists():
            return UserServiceAccess.objects.all()

        return UserServiceAccess.objects.filter(user=user)

    def perform_create(self, serializer):
        user = serializer.validated_data.get('user')

        if user.is_superuser:
            raise PermissionDenied("Você não pode modificar permissões do superusuário.")

        if UserServiceAccess.objects.filter(user=user).exists():
            raise serializers.ValidationError("Usuário já possui controle de acesso.")

        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user.is_superuser:
            raise PermissionDenied("Você não pode alterar o superusuário.")

        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user.is_superuser:
            raise PermissionDenied("Você não pode alterar o superusuário.")

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user.is_superuser:
            raise PermissionDenied("Você não pode excluir o superusuário.")

        return super().destroy(request, *args, **kwargs)

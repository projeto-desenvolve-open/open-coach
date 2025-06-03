# services/models/access_control.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserServiceAccess(models.Model):
    """
    Define os módulos aos quais cada usuário tem acesso.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='service_access')
    can_access_crm = models.BooleanField(default=False)
    can_access_tickets = models.BooleanField(default=False)
    can_access_monitoring = models.BooleanField(default=False)
    can_access_seletivo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Acessos de {self.user.email}"

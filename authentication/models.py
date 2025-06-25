from django.db import models

# Create your models here.
import random
import uuid
from datetime import timedelta

from django.db import models
from django.utils.timezone import now, make_aware
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class OtpCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['user', 'is_used']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def is_valid(self):
        """
        Verifica se o código OTP é válido:
        - Gerado há menos de 15 minutos
        - Ainda não foi usado
        """
        current_time = now()
        if settings.USE_TZ and self.created_at.tzinfo is None:
            self.created_at = make_aware(self.created_at)
        return current_time - self.created_at <= timedelta(minutes=15) and not self.is_used

    def mark_as_used(self):
        """Marca o código OTP como utilizado"""
        self.is_used = True
        self.save()

    @staticmethod
    def generate_otp():
        """Gera um código OTP aleatório de 6 dígitos"""
        return ''.join(random.choices("0123456789", k=6))

    @staticmethod
    def clean_expired_codes():
        """
        Exclui todos os códigos que já expiraram (15 minutos)
        ou que já foram utilizados.
        """
        expiration_time = now() - timedelta(minutes=15)
        OtpCode.objects.filter(created_at__lt=expiration_time).delete()
        OtpCode.objects.filter(is_used=True).delete()


class ResetPasswordToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.token}"

    def is_valid(self):
        """Verifica se o token de reset ainda é válido (até 15 minutos)"""
        return now() - self.created_at <= timedelta(minutes=15)

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from authentication.models import OtpCode, ResetPasswordToken
from django.conf import settings
from services.utils.email_service import EmailService
from django.contrib.auth.models import Group

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializador para registrar um usuário e retornar tokens JWT"""
    
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'password2']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este e-mail já está em uso.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(username=validated_data['email'], **validated_data)

        # Adiciona o grupo padrão "user"
        default_group, _ = Group.objects.get_or_create(name='user')
        user.groups.add(default_group)

        refresh = RefreshToken.for_user(user)
        groups = user.groups.values_list('name', flat=True)

        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": groups[0] if groups else "user",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserLoginSerializer(serializers.Serializer):
    """Serializador para autenticação de usuários e geração de tokens"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Credenciais inválidas.")

        refresh = RefreshToken.for_user(user)
        groups = user.groups.values_list('name', flat=True)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": groups[0] if groups else "user"
            },
        }


class UserRecoverySerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("E-mail não encontrado.")

        otp_code = OtpCode.objects.create(user=user, code=OtpCode.generate_otp())

        email_service = EmailService(
            subject="Código de Recuperação de Senha",
            to_email=[value],
            template_name="emails/recovery_email.html",
            context={"otp_code": otp_code.code, "user": user}
        )
        email_service.send()
        
        return value


class OtpVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        """Valida o código OTP e gera um link temporário para redefinição de senha"""
        try:
            otp = OtpCode.objects.filter(code=data['code'], is_used=False).latest('created_at')
        except OtpCode.DoesNotExist:
            raise serializers.ValidationError({"code": "Código inválido ou expirado."})

        if not otp.is_valid():
            otp.delete()  # Limpa o OTP se estiver expirado
            raise serializers.ValidationError({"code": "Código expirado."})

        # Apagar diretamente após validação
        user = otp.user
        otp.delete()

        # Criar token de reset
        reset_token = ResetPasswordToken.objects.create(user=user)

        # Montar URL de reset
        domain = settings.SITE_URL if hasattr(settings, 'SITE_URL') else "http://127.0.0.1"
        reset_url = f"{domain}/auth/reset-password/?token={reset_token.token}"

        return {"reset_url": reset_url}


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})

        try:
            reset_token = ResetPasswordToken.objects.get(token=data['token'])
        except ResetPasswordToken.DoesNotExist:
            raise serializers.ValidationError("Token inválido ou expirado.")

        if not reset_token.is_valid():
            raise serializers.ValidationError("Token expirado.")

        return data

    def save(self):
        reset_token = ResetPasswordToken.objects.get(token=self.validated_data['token'])
        user = reset_token.user
        user.set_password(self.validated_data['password'])
        user.save()

        reset_token.delete()

        email_service = EmailService(
            subject="Sua senha foi alterada",
            to_email=[user.email],
            template_name="emails/password_changed.html",
            context={"user": user}
        )
        email_service.send()

        return {"message": "Senha redefinida com sucesso!"}

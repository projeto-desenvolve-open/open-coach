from rest_framework import serializers
from services.models.access_control import UserServiceAccess
from django.contrib.auth import get_user_model

User = get_user_model()

class UserServiceAccessSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserServiceAccess
        fields = '__all__'
        read_only_fields = ['id', 'user_email']

    def get_field_names(self, declared_fields, info):
        """
        Retorna todos os campos dinamicamente, incluindo os campos booleanos
        adicionados ao modelo.
        """
        default_fields = super().get_field_names(declared_fields, info)
        model_fields = [f.name for f in self.Meta.model._meta.get_fields() if not f.is_relation or f.one_to_one]
        return list(set(default_fields + model_fields))

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        groups = user.groups.values_list('name', flat=True)

        data['role'] = groups[0] if groups else 'user'
        data['user_id'] = user.id
        data['email'] = user.email
        return data

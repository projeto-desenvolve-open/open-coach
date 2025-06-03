from django.contrib import admin
from services.models.access_control import UserServiceAccess

class UserServiceAccessAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        """
        Torna o list_display dinâmico com base nos campos do modelo.
        """
        fields = [f.name for f in UserServiceAccess._meta.fields]
        return fields

admin.site.register(UserServiceAccess, UserServiceAccessAdmin)

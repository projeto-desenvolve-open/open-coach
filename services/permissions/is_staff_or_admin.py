# services/permissions/is_staff_or_admin.py
from rest_framework.permissions import BasePermission

class IsStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=["admin", "staff"]).exists()

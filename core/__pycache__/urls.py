from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# Swagger / Redoc
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ViewSets
from authentication.views import (
    UserRegisterViewSet,
    UserLoginViewSet,
    UserBlockViewSet,
    UserRecoveryViewSet,
    OtpVerifyViewSet,
    ResetPasswordViewSet,
)
from analysis.views import AnalysisViewSet  # <- IMPORTAÇÃO CORRETA

# Documentação Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="BackOffice API",
        default_version="v2",
        description="Documentação da API do Open Posting V2",
        terms_of_service="https://pdinfinita.dev/terms/",
        contact=openapi.Contact(email="suporte@pdinfinita.dev"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
)

# Routers
auth_router = SimpleRouter()
auth_router.register(r'auth/register', UserRegisterViewSet, basename='user-register')
auth_router.register(r'auth/login', UserLoginViewSet, basename='user-login')
auth_router.register(r'auth/block', UserBlockViewSet, basename='user-block')
auth_router.register(r'auth/recovery', UserRecoveryViewSet, basename='user-recovery')
auth_router.register(r'auth/otp-verify', OtpVerifyViewSet, basename='otp-verify')
auth_router.register(r'auth/reset-password', ResetPasswordViewSet, basename='reset-password')

analysis_router = SimpleRouter()
analysis_router.register(r'analysis', AnalysisViewSet, basename='analysis')

# API ROOT – lista os principais endpoints
@api_view(['GET'])
def api_root(request, format=None):
    def uri(path): return request.build_absolute_uri(path)

    return Response({
        # Auth
        "auth/register": uri('auth/register/'),
        "auth/login": uri('auth/login/'),
        "auth/block": uri('auth/block/'),
        "auth/recovery": uri('auth/recovery/'),
        "auth/otp-verify": uri('auth/otp-verify/'),
        "auth/reset-password": uri('auth/reset-password/'),
        "auth/refresh": uri('auth/refresh/'),
        "auth/verify": uri('auth/verify/'),

        # Analysis
        "analysis/analisar": uri('analysis/analisar/'),
        "analysis/tag": uri('analysis/tag/'),
        "analysis/tema-ia": uri('analysis/tema-ia/'),
        "analysis/capitulo-ia": uri('analysis/capitulo-ia/'),
        "analysis/criar-tema-especifico": uri('analysis/criar-tema-especifico/'),

        # Serviços
        "services/access-control": uri('services/access-control/'),

        # Post
        "post/process": uri('post/process/'),
        "post/store": uri('post/store/'),
        "post/upload": uri('post/upload/'),
        "post/prepare-course": uri('post/prepare-course/'),

        # Docs
        "swagger": uri('swagger/'),
        "redoc": uri('redoc/'),
    })

# URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),

    path('', include(auth_router.urls)),
    path('', include(analysis_router.urls)),

    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('services/', include('services.urls')),
    
    path('post/', include('post.urls')),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

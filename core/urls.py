# core/core/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import views from coach and authentication
from coach.views import (
    InitialComparisonData,
    ProfessorsList,
    CompareProfessors,
    StudentsByTurma,
    CompareStudentsInTurma,
    CompareStudentsBetweenTurmas,
    StudentsByProfessor,
    TurmasList,
    CompareClasses,
    PingView,
    StudentResourcesView,
    StudentStudyPlanView,
    StudentGradesView,
    StudentSimuladoView,
    LoginView,
    ChatStudentView,
    ChatTeacherView,
    CoursesView,
    CourseContentView,
    StudentGradesByIdView,
    SpecificStudentGradeView,
    AllStudentGradesView,
    GetStudentGradesOnly,
    GradesByUsernameView,
    AllStudentGradesTeacherView,
    CompareCitiesView,
    CourseContentTeacherView,
    GenerateFeedbackView,
    GenerateExercisesView,
    GenerateClassExercisesView,
    GradesByCityView,
    StudyPlanView,
    TeachingMaterialsView,
)
from authentication.views import (
    UserRegisterViewSet,
    UserLoginViewSet,
    UserBlockViewSet,
    UserRecoveryViewSet,
    OtpVerifyViewSet,
    ResetPasswordViewSet,
)

# Swagger Documentation
schema_view = get_schema_view(
    openapi.Info(
        title="MyCoach API",
        default_version="v2",
        description="API documentation for MyCoach application",
        terms_of_service="https://pdinfinita.dev/terms/",
        contact=openapi.Contact(email="suporte@pdinfinita.dev"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
)

# Routers for authentication
auth_router = SimpleRouter()
auth_router.register(r'auth/register', UserRegisterViewSet, basename='user-register')
auth_router.register(r'auth/login', UserLoginViewSet, basename='user-login')
auth_router.register(r'auth/block', UserBlockViewSet, basename='user-block')
auth_router.register(r'auth/recovery', UserRecoveryViewSet, basename='user-recovery')
auth_router.register(r'auth/otp-verify', OtpVerifyViewSet, basename='otp-verify')
auth_router.register(r'auth/reset-password', ResetPasswordViewSet, basename='reset-password')

# API root endpoint
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
        # General
        "ping": uri('ping/'),
        "courses": uri('courses/'),
        # Student
        "student/resources": uri('student/resources/'),
        "student/study-plan": uri('student/study-plan/'),
        "student/grades": uri('student/grades/'),
        "student/simulado": uri('student/simulado/'),
        "student-grades": uri('student-grades/'),
        "grades": uri('grades/'),
        "specific-grade": uri('grades/'),
        # Teacher
        "teacher/all-grades": uri('teacher-options/all-grades/'),
        "teacher/compare-cities": uri('teacher-options/compare-cities/'),
        "teacher/grades-by-username": uri('teacher-options/grades-by-username/'),
        "teacher/course-content": uri('teacher-options/course-content/'),
        "teacher/feedback": uri('teacher-options/feedback/'),
        "teacher/exercises": uri('teacher-options/exercises/'),
        "teacher/class-exercises": uri('teacher-options/class-exercises/'),
        "teacher/grades-by-city": uri('teacher-options/grades-by-city/'),
        # Study Plan and Materials
        "study-plan": uri('study-plan/'),
        "teaching-materials": uri('teaching-materials/'),
        # Chat
        "chat/student": uri('chat/student/'),
        "chat/teacher": uri('chat/teacher/'),
        # Docs
        "swagger": uri('swagger/'),
        "redoc": uri('redoc/'),
    })

# URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),
    path('ping/', PingView.as_view(), name='ping'),
    path('student/resources/<str:student_email>/', StudentResourcesView.as_view(), name='student_resources'),
    path('student/study-plan/<str:student_email>/', StudentStudyPlanView.as_view(), name='student_study_plan'),
    path('student/grades/<str:student_email>/', StudentGradesView.as_view(), name='student_grades'),
    path('student/simulado/<str:student_email>/', StudentSimuladoView.as_view(), name='student_simulado'),
    path('login/', LoginView.as_view(), name='login'),
    path('chat/student/', ChatStudentView.as_view(), name='chat_student'),
    path('chat/teacher/', ChatTeacherView.as_view(), name='chat_teacher'),
    path('courses/', CoursesView.as_view(), name='courses'),
    path('course-content/<str:course_id>/', CourseContentView.as_view(), name='course_content'),
    path('grades/<int:student_id>/', StudentGradesByIdView.as_view(), name='student_grades_by_id'),
    path('grades/<str:student_email>/<str:course_id>/', SpecificStudentGradeView.as_view(), name='specific_student_grade'),
    path('student-grades/<str:student_email>/', AllStudentGradesView.as_view(), name='all_student_grades'),
    path('teacher-options/grades-by-username/<str:username>/', GradesByUsernameView.as_view(), name='grades_by_username'),
    path('teacher-options/all-grades/', AllStudentGradesTeacherView.as_view(), name='all_student_grades_teacher'),
    path('teacher-options/compare-cities/', CompareCitiesView.as_view(), name='compare_cities'),
    path('teacher-options/course-content/<str:course_name>/', CourseContentTeacherView.as_view(), name='course_content_teacher'),
    path('teacher-options/feedback/<str:username>/<str:course_id>/', GenerateFeedbackView.as_view(), name='generate_feedback'),
    path('teacher-options/exercises/<str:username>/<str:course_id>/', GenerateExercisesView.as_view(), name='generate_exercises'),
    path('teacher-options/class-exercises/<str:city>/<str:course_name>/', GenerateClassExercisesView.as_view(), name='generate_class_exercises'),
    path('teacher-options/grades-by-city/<str:city>/', GradesByCityView.as_view(), name='grades_by_city'),
    path('study-plan/', StudyPlanView.as_view(), name='study_plan'),
    path('teaching-materials/', TeachingMaterialsView.as_view(), name='teaching_materials'),
    path('', include(auth_router.urls)),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
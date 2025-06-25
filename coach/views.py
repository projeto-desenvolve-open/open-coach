# core/coach/views.py
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.conf import settings
import jwt
import datetime
import re
import json
import requests
import logging
from .services import (
    get_course_content,
    get_student_grades,
    get_specific_student_grade,
    generate_study_plan,
    generate_teaching_materials,
    get_student_grades_all_courses,
    get_all_student_grades,
    compare_cities,
    get_student_grades_by_username,
    generate_simulado,
    get_student_grades_by_email,
    generate_study_resources,
    generate_study_plan_student,
    get_turmas_list,
    compare_classes,
    get_professors_list,
    compare_professors,
    get_students_by_turma,
    compare_students_in_turma,
    compare_students_between_turmas,
    get_students_by_professor,
    get_initial_comparison_data,
    generate_lesson
)
from .utils import validate_request

logger = logging.getLogger(__name__)

def validate_jwt_token(token):
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return decoded
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {str(e)}")
        return None

class InitialComparisonData(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            result, status_code = get_initial_comparison_data()
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao buscar dados iniciais: {str(e)}")
            return JsonResponse({"error": f"Erro ao buscar dados iniciais: {str(e)}"}, status=500)

class ProfessorsList(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            result, status_code = get_professors_list()
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao buscar lista de professores: {str(e)}")
            return JsonResponse({"error": f"Erro ao buscar professores: {str(e)}"}, status=500)

class CompareProfessors(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        professor1 = request.GET.get('professor1')
        professor2 = request.GET.get('professor2')
        if not professor1 or not professor2:
            logger.error("Missing professor1 or professor2 parameters")
            return JsonResponse({"error": "Parâmetros professor1 e professor2 são obrigatórios"}, status=400)
        try:
            result, status_code = compare_professors(professor1, professor2)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao comparar professores: {str(e)}")
            return JsonResponse({"error": f"Erro ao comparar professores: {str(e)}"}, status=500)

class StudentsByTurma(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, turma_name, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            result, status_code = get_students_by_turma(turma_name)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao buscar alunos da turma {turma_name}: {str(e)}")
            return JsonResponse({"error": f"Erro ao buscar alunos: {str(e)}"}, status=500)

class CompareStudentsInTurma(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        turma_name = request.GET.get('turma')
        aluno1 = request.GET.get('aluno1')
        aluno2 = request.GET.get('aluno2')
        if not turma_name or not aluno1 or not aluno2:
            logger.error("Missing turma, aluno1 or aluno2 parameters")
            return JsonResponse({"error": "Parâmetros turma, aluno1 e aluno2 são obrigatórios"}, status=400)
        try:
            result, status_code = compare_students_in_turma(turma_name, aluno1, aluno2)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao comparar alunos: {str(e)}")
            return JsonResponse({"error": f"Erro ao comparar alunos: {str(e)}"}, status=500)

class CompareStudentsBetweenTurmas(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        turma1 = request.GET.get('turma1')
        aluno1 = request.GET.get('aluno1')
        turma2 = request.GET.get('turma2')
        aluno2 = request.GET.get('aluno2')
        if not turma1 or not aluno1 or not turma2 or not aluno2:
            logger.error("Missing turma1, aluno1, turma2 or aluno2 parameters")
            return JsonResponse({"error": "Parâmetros turma1, aluno1, turma2 e aluno2 são obrigatórios"}, status=400)
        try:
            result, status_code = compare_students_between_turmas(turma1, aluno1, turma2, aluno2)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao comparar alunos entre turmas: {str(e)}")
            return JsonResponse({"error": f"Erro ao comparar alunos: {str(e)}"}, status=500)

class StudentsByProfessor(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, professor_name, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            result, status_code = get_students_by_professor(professor_name)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao buscar alunos do professor {professor_name}: {str(e)}")
            return JsonResponse({"error": f"Erro ao buscar alunos: {str(e)}"}, status=500)

class TurmasList(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            result, status_code = get_turmas_list()
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao buscar lista de turmas: {str(e)}")
            return JsonResponse({"error": f"Erro ao buscar turmas: {str(e)}"}, status=500)

class CompareClasses(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        turma1 = request.GET.get('turma1')
        turma2 = request.GET.get('turma2')
        if not turma1 or not turma2:
            logger.error("Missing turma1 or turma2 parameters")
            return JsonResponse({"error": "Parâmetros turma1 e turma2 são obrigatórios"}, status=400)
        try:
            result, status_code = compare_classes(turma1, turma2)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao comparar turmas: {str(e)}")
            return JsonResponse({"error": f"Erro ao comparar turmas: {str(e)}"}, status=500)

class PingView(APIView):
    def get(self, request, *args, **kwargs):
        logger.debug("Received ping request")
        return JsonResponse({"status": "ok"})

class StudentResourcesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, student_email, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        course_name = request.GET.get('course_name')
        if not course_name:
            logger.error("Missing course_name parameter")
            return JsonResponse({"error": "Nome do curso é obrigatório."}, status=400)
        try:
            result, status_code = generate_study_resources(student_email, course_name)
            if status_code != 200:
                logger.error(f"Erro ao gerar recursos: {result.get('error')}")
                return JsonResponse(result, status=status_code)
            if not result.get("resources"):
                return JsonResponse({
                    "student_email": result["student_email"],
                    "username": result["username"],
                    "course_name": result["course_name"],
                    "message": result["message"]
                }, status=200)
            return StreamingHttpResponse(result["resources"], content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao processar recursos: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar recursos: {str(e)}"}, status=500)

class StudentStudyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def post(self, request, student_email, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            data = validate_request(request, ['course_name', 'theory_minutes', 'practice_minutes', 'exercise_minutes', 'grade'])
            if isinstance(data, dict) and 'error' in data:
                logger.error(f"Validation failed: {data}")
                return JsonResponse(data, status=400)
            result = generate_study_plan_student(student_email)
            if isinstance(result, tuple):
                logger.error(f"Erro ao gerar plano: {result[0].get('error')}")
                return JsonResponse(result[0], status=result[1])
            return result
        except Exception as e:
            logger.error(f"Erro ao processar plano: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar plano: {str(e)}"}, status=500)

class StudentGradesView(APIView):
    def get(self, request, student_email, *args, **kwargs):
        result, status_code = get_student_grades_by_email(student_email)
        return JsonResponse(result, status=status_code)

class StudentSimuladoView(APIView):
    def get(self, request, student_email, *args, **kwargs):
        mode = request.GET.get('mode', 'weak')
        course_id = request.GET.get('course_id')
        result, status_code = generate_simulado(student_email, mode, course_id)
        if status_code != 200:
            return JsonResponse(result, status=status_code)
        return StreamingHttpResponse(result['simulado'], content_type='text/plain')

class LoginView(APIView):
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        data = validate_request(request, ['email'])
        if isinstance(data, dict) and 'error' in data:
            logger.error(f"Validation failed: {data}")
            return JsonResponse(data, status=400)
        email = data['email']
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            logger.error(f"Invalid email format: {email}")
            return JsonResponse({"error": "Email inválido"}, status=400)
        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, settings.SECRET_KEY, algorithm='HS256')
        return JsonResponse({"token": token}, status=200)

class ChatStudentView(APIView):
    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def post(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        data = validate_request(request, ['message'])
        if isinstance(data, dict) and 'error' in data:
            return JsonResponse(data, status=400)
        payload = {
            "messages": [
                {"role": "system", "content": "Você é um assistente eficiente para alunos."},
                {"role": "user", "content": data['message']}
            ],
            "stream": True,
            "temperature": 0.55
        }
        try:
            response = requests.post(
                'https://mycoach.tksol.com.br/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json=payload,
                stream=True
            )
            if not response.ok:
                logger.error(f"Error from IA API: {response.status_code} {response.text}")
                return JsonResponse({"error": "Falha na comunicação com a assistente"}, status=500)
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            return StreamingHttpResponse(generate(), content_type='application/json')
        except Exception as e:
            logger.error(f"Error processing IA request: {str(e)}")
            return JsonResponse({"error": "Erro ao processar a requisição"}, status=500)

class ChatTeacherView(APIView):
    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def post(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        data = validate_request(request, ['message'])
        if isinstance(data, dict) and 'error' in data:
            return JsonResponse(data, status=400)
        payload = {
            "messages": [
                {"role": "system", "content": "Você é um assistente para professores, ajude a criar atividades e fornecer feedback sobre ensino de cursos no geral."},
                {"role": "user", "content": data['message']}
            ],
            "stream": True,
            "temperature": 0.55
        }
        try:
            response = requests.post(
                'https://mycoach.tksol.com.br/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json=payload,
                stream=True
            )
            if not response.ok:
                logger.error(f"Error from IA API: {response.status_code} {response.text}")
                return JsonResponse({"error": "Falha na comunicação com a assistente"}, status=500)
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            return StreamingHttpResponse(generate(), content_type='application/json')
        except Exception as e:
            logger.error(f"Error processing IA request: {str(e)}")
            return JsonResponse({"error": "Erro ao processar a requisição"}, status=500)

class CoursesView(APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse(settings.COURSES)

class CourseContentView(APIView):
    def get(self, request, course_id, *args, **kwargs):
        chapter = request.GET.get('chapter', '1')
        section = request.GET.get('section', 'contextualizando')
        content = get_course_content(course_id, chapter, section)
        return JsonResponse(content)

class StudentGradesByIdView(APIView):
    def get(self, request, student_id, *args, **kwargs):
        grades = get_student_grades(student_id)
        return JsonResponse(grades)

class SpecificStudentGradeView(APIView):
    def get(self, request, student_email, course_id, *args, **kwargs):
        result, status_code = get_specific_student_grade(student_email, course_id)
        return JsonResponse(result, status=status_code)

class AllStudentGradesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, student_email, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        result, status_code = get_student_grades_all_courses(student_email)
        if status_code != 200:
            logger.error(f"Erro ao buscar notas: {result.get('error')}")
            return JsonResponse(result, status=status_code)
        return JsonResponse(result, status=200)

class GetStudentGradesOnly(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, student_email, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            result, status_code = get_student_grades_by_email(student_email)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao buscar notas: {str(e)}")
            return JsonResponse({"error": f"Erro ao buscar notas: {str(e)}"}, status=500)

class StudyPlanView(APIView):
    def post(self, request, *args, **kwargs):
        data = validate_request(request, ['student_id', 'course_id', 'weak_subjects'])
        if isinstance(data, dict) and 'error' in data:
            return JsonResponse(data, status=400)
        plan = generate_study_plan(
            data['student_id'],
            data['course_id'],
            data['weak_subjects']
        )
        return JsonResponse(plan)

class TeachingMaterialsView(APIView):
    def post(self, request, *args, **kwargs):
        data = validate_request(request, ['teacher_id', 'course_id', 'material_type'])
        if isinstance(data, dict) and 'error' in data:
            return JsonResponse(data, status=400)
        materials = generate_teaching_materials(
            data['teacher_id'],
            data['course_id'],
            data['material_type']
        )
        return JsonResponse(materials)

class AllStudentGradesTeacherView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return HttpResponse("Missing or invalid Authorization header", status=401, content_type='text/plain')
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return HttpResponse("Invalid JWT token", status=401, content_type='text/plain')
        try:
            generate = get_all_student_grades()
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao buscar todas as notas: {str(e)}")
            return HttpResponse(f"Erro ao buscar notas: {str(e)}", status=500, content_type='text/plain')

class CompareCitiesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return HttpResponse(json.dumps({"error": "Missing or invalid Authorization header"}) + '\n', status=401, content_type='text/plain')
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return HttpResponse(json.dumps({"error": "Invalid JWT token"}) + '\n', status=401, content_type='text/plain')
        try:
            generate = compare_cities()
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao comparar cidades: {str(e)}")
            return HttpResponse(json.dumps({"error": f"Erro ao comparar cidades: {str(e)}"}) + '\n', status=500, content_type='text/plain')

class GradesByUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, username, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        try:
            result, status_code = get_student_grades_by_username(username)
            return JsonResponse(result, status=status_code)
        except Exception as e:
            logger.error(f"Erro ao buscar notas do aluno {username}: {str(e)}")
            return JsonResponse({"error": f"Erro ao buscar notas: {str(e)}"}, status=500)

class CourseContentTeacherView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def post(self, request, course_name, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        data = validate_request(request, ['message'])
        if isinstance(data, dict) and 'error' in data:
            logger.error(f"Validation failed: {data}")
            return JsonResponse(data, status=400)
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": "Você é um assistente educacional especializado em criar planos de aula envolventes."},
                    {"role": "user", "content": data['message']}
                ],
                "stream": True,
                "temperature": 0.55
            }
            response = requests.post(
                'https://mycoach.tksol.com.br/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json=payload,
                stream=True
            )
            if not response.ok:
                error_data = response.json()
                logger.error(f"Erro na API xAI: {error_data}")
                return JsonResponse({"error": f"Erro ao gerar plano de aula: {error_data.get('error', 'Unknown error')}"}, status=500)
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao processar plano de aula: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar plano de aula: {str(e)}"}, status=500)

class GenerateFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def post(self, request, username, course_id, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        data = validate_request(request, ['message'])
        if isinstance(data, dict) and 'error' in data:
            logger.error(f"Validation failed: {data}")
            return JsonResponse(data, status=400)
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": "Você é um assistente educacional especializado em fornecer feedback personalizado e profissional para alunos."},
                    {"role": "user", "content": data['message']}
                ],
                "stream": True,
                "temperature": 0.55
            }
            response = requests.post(
                'https://mycoach.tksol.com.br/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json=payload,
                stream=True
            )
            if not response.ok:
                error_data = response.json()
                logger.error(f"Erro na API xAI: {error_data}")
                return JsonResponse({"error": f"Erro ao gerar feedback: {error_data.get('error', 'Unknown error')}"}, status=500)
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao processar feedback: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar feedback: {str(e)}"}, status=500)

class GenerateExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def post(self, request, username, course_id, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        data = validate_request(request, ['message'])
        if isinstance(data, dict) and 'error' in data:
            logger.error(f"Validation failed: {data}")
            return JsonResponse(data, status=400)
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": "Você é um assistente educacional especializado em criar exercícios práticos e profissionais para alunos."},
                    {"role": "user", "content": data['message']}
                ],
                "stream": True,
                "temperature": 0.55
            }
            response = requests.post(
                'https://mycoach.tksol.com.br/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json=payload,
                stream=True
            )
            if not response.ok:
                error_data = response.json()
                logger.error(f"Erro na API xAI: {error_data}")
                return JsonResponse({"error": f"Erro ao gerar exercícios: {error_data.get('error', 'Unknown error')}"}, status=500)
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao processar exercícios: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar exercícios: {str(e)}"}, status=500)

class GenerateClassExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def post(self, request, city, course_name, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        if city not in ['PDBD', 'PDITA']:
            logger.error(f"Invalid city: {city}")
            return JsonResponse({"error": "Cidade inválida. Use PDBD ou PDITA."}, status=400)
        data = validate_request(request, ['message'])
        if isinstance(data, dict) and 'error' in data:
            logger.error(f"Validation failed: {data}")
            return JsonResponse(data, status=400)
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": "Você é um assistente educacional especializado em criar exercícios práticos e profissionais para turmas."},
                    {"role": "user", "content": data['message']}
                ],
                "stream": True,
                "temperature": 0.55
            }
            response = requests.post(
                'https://mycoach.tksol.com.br/v1/chat/completions',
                headers={'Content-Type': 'application/json'},
                json=payload,
                stream=True
            )
            if not response.ok:
                error_data = response.json()
                logger.error(f"Erro na API xAI: {error_data}")
                return JsonResponse({"error": f"Erro ao gerar exercícios: {error_data.get('error', 'Unknown error')}"}, status=500)
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao processar exercícios para turma: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar exercícios: {str(e)}"}, status=500)

class GradesByCityView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='10/m'))
    def get(self, request, city, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        if city not in ['PDBD', 'PDITA']:
            logger.error(f"Invalid city: {city}")
            return JsonResponse({"error": "Cidade inválida. Use PDBD ou PDITA."}, status=400)
        try:
            grades_data = load_grades_data()
            if isinstance(grades_data, dict) and 'error' in grades_data:
                logger.error(f"Erro ao carregar dados: {grades_data['error']}")
                return JsonResponse({"error": grades_data['error']}, status=grades_data.get("status", 500))
            if not grades_data:
                logger.warning(f"No data found in all_grades.json for city {city}")
                return JsonResponse({"grades": [], "message": f"Nenhum dado encontrado em all_grades.json para a cidade {city}"}, status=200)
            city_grades = []
            city_students = set()
            course_summary = {}
            student_count = 0
            for course_id, course_data in grades_data.items():
                course_name = course_data.get("course_name", course_id)
                logger.debug(f"Processing course: {course_id} ({course_name})")
                grades_list = course_data.get("grades", [])
                grades_count = len(grades_list)
                logger.debug(f"Total students in {course_id}: {grades_count}")
                if grades_count == 0:
                    logger.debug(f"No grades found for course {course_id}")
                    continue
                for grade in grades_list:
                    username = grade.get("username", "").lower()
                    user_id = grade.get("user_id", 0)
                    calculated_grade = grade.get("calculated_grade", 0.0)
                    if not username or user_id is None:
                        logger.warning(f"Invalid grade entry in {course_id}: username={username}, user_id={user_id}")
                        continue
                    if "pdita" in username:
                        assigned_city = "PDITA"
                    elif "pdbd" in username:
                        assigned_city = "PDBD"
                    else:
                        assigned_city = "PDITA" if user_id % 2 else "PDBD"
                    if assigned_city == city:
                        logger.debug(f"Assigned {username} to {city}, grade: {calculated_grade}")
                        city_grades.append(calculated_grade)
                        city_students.add(user_id)
                        student_count += 1
                        if course_name not in course_summary:
                            course_summary[course_name] = {"grades": [], "students": set()}
                        course_summary[course_name]["grades"].append(calculated_grade)
                        course_summary[course_name]["students"].add(user_id)
            logger.debug(f"Total students assigned to {city}: {student_count}")
            if not city_grades:
                logger.info(f"No grades found for city {city} after processing")
                return JsonResponse({"grades": [], "message": f"Nenhuma nota encontrada para a cidade {city}"}, status=200)
            grades = [
                {
                    "course_name": course_name,
                    "average_grade": round(sum(data["grades"]) / len(data["grades"]), 2) if data["grades"] else 0,
                    "student_count": len(data["students"])
                }
                for course_name, data in course_summary.items()
            ]
            return JsonResponse({"grades": grades}, status=200)
        except FileNotFoundError as e:
            logger.error(f"Arquivo all_grades.json não encontrado: {str(e)}")
            return JsonResponse({"error": "Arquivo de notas não encontrado no servidor"}, status=500)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar all_grades.json: {str(e)}")
            return JsonResponse({"error": "Formato inválido no arquivo de notas"}, status=500)
        except Exception as e:
            logger.error(f"Erro ao buscar notas da cidade {city}: {str(e)}")
            return JsonResponse({"error": f"Erro interno ao buscar notas: {str(e)}"}, status=500)

class GenerateStudentSimuladoView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def get(self, request, student_email, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        mode = request.GET.get('mode', 'weak')
        if mode not in ['weak', 'strong']:
            logger.error(f"Invalid mode: {mode}")
            return JsonResponse({"error": "Modo inválido. Use 'weak' ou 'strong'."}, status=400)
        try:
            result, status_code = generate_simulado(student_email, mode=mode)
            if status_code != 200:
                logger.error(f"Erro ao gerar simulado: {result.get('error')}")
                return JsonResponse(result, status=status_code)
            if not result.get("simulado"):
                return JsonResponse({
                    "student_email": result["student_email"],
                    "username": result["username"],
                    "grades": result["grades"],
                    "message": result["message"]
                }, status=200)
            def generate():
                yield json.dumps({
                    "type": "grades",
                    "student_email": result["student_email"],
                    "username": result["username"],
                    "grades": result["grades"]
                }) + '\n'
                for chunk in result["simulado"]:
                    yield chunk
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao processar simulado: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar simulado: {str(e)}"}, status=500)

class CreateLessonView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key='ip', rate='5/m'))
    def post(self, request, *args, **kwargs):
        if request.method == 'OPTIONS':
            return JsonResponse({}, status=200)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)
        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)
        data = validate_request(request, ['subject', 'lesson_number'])
        if isinstance(data, dict) and 'error' in data:
            logger.error(f"Validation failed: {data}")
            return JsonResponse(data, status=400)
        subject = data['subject']
        lesson_number = data['lesson_number']
        try:
            result = generate_lesson(subject, lesson_number)
            if isinstance(result, tuple):
                logger.error(f"Erro ao gerar aula: {result[0].get('error')}")
                return JsonResponse(result[0], status=result[1])
            return result
        except Exception as e:
            logger.error(f"Erro ao processar aula: {str(e)}")
            return JsonResponse({"error": f"Erro ao processar aula: {str(e)}"}, status=500)
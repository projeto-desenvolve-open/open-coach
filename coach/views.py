from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.http import StreamingHttpResponse, JsonResponse
from django.conf import settings
from .services import (
    generate_study_resources,
    generate_study_plan_student,
    get_student_grades_by_email,
    generate_simulado,
    get_student_grades_all_courses,
    get_student_grades_by_username,
    get_course_content,
    get_student_grades,
    get_specific_student_grade,
    get_all_student_grades,
    compare_cities,
    generate_study_plan,
    generate_teaching_materials,
)
from .utils import validate_request
import jwt
import re
import logging
import json
import requests
import datetime

logger = logging.getLogger(__name__)

class FivePerMinuteThrottle(UserRateThrottle):
    rate = '5/minute'

class TenPerMinuteThrottle(UserRateThrottle):
    rate = '10/minute'

def validate_jwt_token(token):
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        return decoded
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {str(e)}")
        return None

class PingView(APIView):
    def get(self, request):
        logger.debug("Received ping request")
        response = JsonResponse({"status": "ok"})
        response['Access-Control-Allow-Origin'] = '*'
        return response

class StudentResourcesView(APIView):
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, student_email):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request, student_email):
        logger.debug(f"Received GET request to /api/student/resources/{student_email}")
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

        result, status_code = generate_study_resources(student_email, course_name)
        if status_code != 200:
            logger.error(f"Erro ao gerar recursos: {result.get('error')}")
            return JsonResponse(result, status=status_code)

        if not result.get("resources"):
            response = JsonResponse({
                "student_email": result["student_email"],
                "username": result["username"],
                "course_name": result["course_name"],
                "message": result["message"]
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response

        return StreamingHttpResponse(result["resources"], content_type='text/plain; charset=utf-8')

class StudentStudyPlanView(APIView):
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, student_email):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request, student_email):
        logger.debug(f"Received POST request to /api/student/study-plan/{student_email}")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)

        result, status_code = generate_study_plan_student(student_email, request.data)
        if status_code != 200:
            logger.error(f"Erro ao gerar plano: {result.get('error')}")
            return JsonResponse(result, status=status_code)

        if not result.get("plan"):
            response = JsonResponse({
                "student_email": result["student_email"],
                "username": result["username"],
                "course_name": result["course_name"],
                "message": result["message"]
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response

        return StreamingHttpResponse(result["plan"], content_type='text/plain; charset=utf-8')

class StudentGradesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_email):
        result, status_code = get_student_grades_by_email(student_email)
        response = JsonResponse(result, status=status_code)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class StudentSimuladoView(APIView):
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, student_email):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request, student_email):
        logger.debug(f"Received GET request to /api/student/simulado/{student_email}")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)

        mode = request.GET.get('mode', 'weak')
        course_id = request.GET.get('course_id')
        if mode not in ['weak', 'strong']:
            logger.error(f"Invalid mode: {mode}")
            return JsonResponse({"error": "Modo inválido. Use 'weak' ou 'strong'."}, status=400)

        result, status_code = generate_simulado(student_email, mode, course_id)
        if status_code != 200:
            logger.error(f"Erro ao gerar simulado: {result.get('error')}")
            return JsonResponse(result, status=status_code)

        if not result.get("simulado"):
            response = JsonResponse({
                "student_email": result["student_email"],
                "username": result["username"],
                "grades": result["grades"],
                "message": result["message"]
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response

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

class LoginView(APIView):
    throttle_classes = [TenPerMinuteThrottle]

    def options(self, request):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request):
        logger.debug("Received POST request to /api/login")
        data = validate_request(request, ['email'])
        if isinstance(data, JsonResponse):
            logger.error(f"Validation failed: {data}")
            return data

        email = data['email']
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            logger.error(f"Invalid email format: {email}")
            response = JsonResponse({"error": "Email inválido"})
            response['Access-Control-Allow-Origin'] = '*'
            return response

        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, settings.JWT_SECRET_KEY, algorithm='HS256')
        response = JsonResponse({"token": token})
        response['Access-Control-Allow-Origin'] = '*'
        return response

class ChatStudentView(APIView):
    throttle_classes = [TenPerMinuteThrottle]

    def options(self, request):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request):
        data = validate_request(request, ['message'])
        if isinstance(data, JsonResponse):
            return data

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
    throttle_classes = [TenPerMinuteThrottle]

    def options(self, request):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request):
        data = validate_request(request, ['message'])
        if isinstance(data, JsonResponse):
            return data

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
    def get(self, request):
        return JsonResponse(settings.COURSES)

class CourseContentView(APIView):
    def get(self, request, course_id):
        chapter = request.GET.get('chapter', '1')
        section = request.GET.get('section', 'contextualizando')
        content = get_course_content(course_id, chapter, section)
        return JsonResponse(content)

class StudentGradesByIdView(APIView):
    def get(self, request, student_id):
        grades = get_student_grades(student_id)
        return JsonResponse(grades)

class SpecificStudentGradeView(APIView):
    def get(self, request, student_email, course_id):
        result, status_code = get_specific_student_grade(student_email, course_id)
        return JsonResponse(result, status=status_code)

class AllStudentGradesView(APIView):
    throttle_classes = [TenPerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, student_email):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request, student_email):
        logger.debug(f"Received GET request to /api/student-grades/{student_email}")
        result, status_code = get_student_grades_all_courses(student_email)
        if status_code != 200:
            logger.error(f"Erro ao buscar notas: {result.get('error')}")
            return JsonResponse(result, status=status_code)

        response = JsonResponse(result)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class AllStudentGradesTeacherView(APIView):
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request):
        logger.debug("Received GET request to /api/teacher-options/all-grades")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return Response("Missing or invalid Authorization header", status=401, content_type='text/plain')

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return Response("Invalid JWT token", status=401, content_type='text/plain')

        try:
            generate = get_all_student_grades()
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao buscar todas as notas: {str(e)}")
            return Response(f"Erro ao buscar notas: {str(e)}", status=500, content_type='text/plain')

class CompareCitiesView(APIView):
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request):
        logger.debug("Received GET request to /api/teacher-options/compare-cities")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return Response(json.dumps({"error": "Missing or invalid Authorization header"}) + '\n', status=401, content_type='text/plain')

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return Response(json.dumps({"error": "Invalid JWT token"}) + '\n', status=401, content_type='text/plain')

        try:
            generate = compare_cities()
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except Exception as e:
            logger.error(f"Erro ao comparar cidades: {str(e)}")
            return Response(json.dumps({"error": f"Erro ao comparar cidades: {str(e)}"}) + '\n', status=500, content_type='text/plain')

class GradesByUsernameView(APIView):
    throttle_classes = [TenPerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, username):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request, username):
        logger.debug(f"Received GET request to /api/teacher-options/grades-by-username/{username}")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)

        result, status_code = get_student_grades_by_username(username)
        response = JsonResponse(result, status=status_code)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class CourseContentTeacherView(APIView):
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, course_name):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request, course_name):
        logger.debug(f"Received POST request to /api/teacher-options/course-content/{course_name}")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)

        data = validate_request(request, ['message'])
        if isinstance(data, JsonResponse):
            logger.error(f"Validation failed: {data}")
            return data

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
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, username, course_id):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request, username, course_id):
        logger.debug(f"Received POST request to /api/teacher-options/feedback/{username}/{course_id}")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)

        data = validate_request(request, ['message'])
        if isinstance(data, JsonResponse):
            logger.error(f"Validation failed: {data}")
            return data

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
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, username, course_id):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request, username, course_id):
        logger.debug(f"Received POST request to /api/teacher-options/exercises/{username}/{course_id}")
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.error("Missing or invalid Authorization header")
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

        token = auth_header.split(' ')[1]
        if not validate_jwt_token(token):
            logger.error("Invalid JWT token")
            return JsonResponse({"error": "Invalid JWT token"}, status=401)

        data = validate_request(request, ['message'])
        if isinstance(data, JsonResponse):
            logger.error(f"Validation failed: {data}")
            return data

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
    throttle_classes = [FivePerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, city, course_name):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def post(self, request, city, course_name):
        logger.debug(f"Received POST request to /api/teacher-options/class-exercises/{city}/{course_name}")
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
        if isinstance(data, JsonResponse):
            logger.error(f"Validation failed: {data}")
            return data

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
    throttle_classes = [TenPerMinuteThrottle]
    permission_classes = [IsAuthenticated]

    def options(self, request, city):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request, city):
        logger.debug(f"Received GET request to /api/teacher-options/grades-by-city/{city}")
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

            response = JsonResponse({"grades": grades})
            response['Access-Control-Allow-Origin'] = '*'
            return response
        except FileNotFoundError as e:
            logger.error(f"Arquivo all_grades.json não encontrado: {str(e)}")
            return JsonResponse({"error": "Arquivo de notas não encontrado no servidor"}, status=500)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar all_grades.json: {str(e)}")
            return JsonResponse({"error": "Formato inválido no arquivo de notas"}, status=500)
        except Exception as e:
            logger.error(f"Erro ao buscar notas da cidade {city}: {str(e)}")
            return JsonResponse({"error": f"Erro interno ao buscar notas: {str(e)}"}, status=500)

class StudyPlanView(APIView):
    def post(self, request):
        data = validate_request(request, ['student_id', 'course_id', 'weak_subjects'])
        if isinstance(data, JsonResponse):
            return data
        
        plan = generate_study_plan(
            data['student_id'],
            data['course_id'],
            data['weak_subjects']
        )
        return JsonResponse(plan)

class TeachingMaterialsView(APIView):
    def post(self, request):
        data = validate_request(request, ['teacher_id', 'course_id', 'material_type'])
        if isinstance(data, JsonResponse):
            return data
        
        materials = generate_teaching_materials(
            data['teacher_id'],
            data['course_id'],
            data['material_type']
        )
        return JsonResponse(materials)
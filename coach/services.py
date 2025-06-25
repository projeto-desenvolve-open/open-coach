# core/coach/services.py
import requests
from bs4 import BeautifulSoup
import os
import json
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.http import StreamingHttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

GRADES_FILE_PATH = os.path.join(settings.BASE_DIR, 'coach', 'data', 'all_grades.json')
NEW_GRADES_FILE_PATH = os.path.join(settings.BASE_DIR, 'coach', 'data', 'new_grades.json')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "https://mycoach.tksol.com.br/v1/chat/completions")
BASE_URL = "https://projetodesenvolve.online"
CLIENT_ID = os.getenv("CLIENT_ID", "mycoach-consumer")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "0vpaOnw1lzL0iaGSEcGjkUusclqHscYkWPrH1tA9fU48AvX0C9eeWO1iy2Yi3wwjdUilrAQzT3PyXbC2qW2s8rDINDo6dnpNDv2ZiXlGHOjRMp2AuzG8BAmHtpeX0Orb")
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "X58cN20jI3qM")

# Load courses from cursos.json (already in settings.py)
COURSES = settings.COURSES

# Rest of the services.py content (generate_lesson, get_professors_list, etc.)
def generate_lesson(subject, lesson_number):
    prompt = f"""
    Crie uma aula profissional e estruturada para professores sobre o tema '{subject}'.
    Esta é a Aula {lesson_number}. Forneça uma introdução, objetivos, conteúdo detalhado (com subtemas ou tópicos),
    atividades práticas, e uma conclusão. Inclua dicas para engajamento dos alunos e recursos adicionais.
    Formate o texto em português (Brasil) com seções claras:
    ## Aula {lesson_number}: {subject}
    ### Introdução
    [Breve contexto sobre o tema]
    ### Objetivos
    - [Objetivo 1]
    - [Objetivo 2]
    ### Conteúdo
    - [Subtema 1: Descrição]
    - [Subtema 2: Descrição]
    ### Atividades Práticas
    - [Atividade 1]
    - [Atividade 2]
    ### Conclusão
    - [Resumo e próximos passos]
    ### Dicas de Engajamento
    - [Dica 1]
    - [Dica 2]
    ### Recursos Adicionais
    - [Recurso 1]
    - [Recurso 2]
    """
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.post(
            API_BASE_URL,
            json={
                "messages": [
                    {"role": "system", "content": "Você é um assistente educacional especializado em criar aulas profissionais para professores."},
                    {"role": "user", "content": prompt}
                ],
                "stream": True,
                "temperature": 0.55
            },
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        response.raise_for_status()
        def generate():
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    decoded_chunk = chunk.decode('utf-8')
                    yield decoded_chunk
            yield "\n[DONE]\n"
        return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return {"error": f"Erro ao gerar aula: {str(e)}"}, 500

def get_professors_list():
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        professors = [
            {"nome": prof["nome"], "materia": prof["materia"], "turmas": prof["turmas"]}
            for prof in grades_data.get("professores", [])
        ]
        return {"professores": professors}, 200
    except Exception as e:
        logger.error(f"Erro ao listar professores: {str(e)}")
        return {"error": f"Erro ao listar professores: {str(e)}"}, 500

def compare_professors(professor1, professor2):
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        professors = grades_data.get("professores", [])
        prof1_data = next((p for p in professors if p["nome"] == professor1), None)
        prof2_data = next((p for p in professors if p["nome"] == professor2), None)
        if not prof1_data or not prof2_data:
            return {"error": f"Um ou ambos os professores ({professor1}, {professor2}) não encontrados"}, 404
        turmas = grades_data.get("turmas", [])
        comparison_data = {
            professor1: {"materia": prof1_data["materia"], "nota_professor": prof1_data["nota"], "turmas": {}, "average_grade": 0, "student_count": 0},
            professor2: {"materia": prof2_data["materia"], "nota_professor": prof2_data["nota"], "turmas": {}, "average_grade": 0, "student_count": 0}
        }
        prof1_grades = []
        prof1_student_count = 0
        for turma_name in prof1_data["turmas"]:
            turma_data = next((t for t in turmas if t["nome"] == turma_name), None)
            if turma_data:
                comparison_data[professor1]["turmas"][turma_name] = {"students": len(turma_data["alunos"]), "average_grade": 0}
                materia = prof1_data["materia"]
                grades = [aluno["notas"][materia] for aluno in turma_data["alunos"]]
                if grades:
                    avg_grade = sum(grades) / len(grades)
                    comparison_data[professor1]["turmas"][turma_name]["average_grade"] = round(avg_grade, 2)
                    prof1_grades.extend(grades)
                    prof1_student_count += len(grades)
        comparison_data[professor1]["average_grade"] = round(sum(prof1_grades) / len(prof1_grades), 2) if prof1_grades else 0
        comparison_data[professor1]["student_count"] = prof1_student_count
        prof2_grades = []
        prof2_student_count = 0
        for turma_name in prof2_data["turmas"]:
            turma_data = next((t for t in turmas if t["nome"] == turma_name), None)
            if turma_data:
                comparison_data[professor2]["turmas"][turma_name] = {"students": len(turma_data["alunos"]), "average_grade": 0}
                materia = prof2_data["materia"]
                grades = [aluno["notas"][materia] for aluno in turma_data["alunos"]]
                if grades:
                    avg_grade = sum(grades) / len(grades)
                    comparison_data[professor2]["turmas"][turma_name]["average_grade"] = round(avg_grade, 2)
                    prof2_grades.extend(grades)
                    prof2_student_count += len(grades)
        comparison_data[professor2]["average_grade"] = round(sum(prof2_grades) / len(prof2_grades), 2) if prof2_grades else 0
        comparison_data[professor2]["student_count"] = prof2_student_count
        return comparison_data, 200
    except Exception as e:
        logger.error(f"Erro ao comparar professores: {str(e)}")
        return {"error": f"Erro ao comparar professores: {str(e)}"}, 500

def get_students_by_turma(turma_name):
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        turmas = grades_data.get("turmas", [])
        turma_data = next((t for t in turmas if t["nome"] == turma_name), None)
        if not turma_data:
            return {"error": f"Turma {turma_name} não encontrada"}, 404
        students = [
            {"nome": aluno["nome"], "notas": aluno["notas"], "media_geral": round(sum(aluno["notas"].values()) / len(aluno["notas"]), 2)}
            for aluno in turma_data["alunos"]
        ]
        return {"turma": turma_name, "alunos": students, "materias": turma_data["materias"]}, 200
    except Exception as e:
        logger.error(f"Erro ao listar alunos da turma {turma_name}: {str(e)}")
        return {"error": f"Erro ao listar alunos: {str(e)}"}, 500

def compare_students_in_turma(turma_name, aluno1, aluno2):
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        turmas = grades_data.get("turmas", [])
        turma_data = next((t for t in turmas if t["nome"] == turma_name), None)
        if not turma_data:
            return {"error": f"Turma {turma_name} não encontrada"}, 404
        aluno1_data = next((a for a in turma_data["alunos"] if a["nome"] == aluno1), None)
        aluno2_data = next((a for a in turma_data["alunos"] if a["nome"] == aluno2), None)
        if not aluno1_data or not aluno2_data:
            return {"error": f"Um ou ambos os alunos ({aluno1}, {aluno2}) não encontrados na turma {turma_name}"}, 404
        comparison_data = {
            "turma": turma_name,
            aluno1: {
                "notas": aluno1_data["notas"],
                "media_geral": round(sum(aluno1_data["notas"].values()) / len(aluno1_data["notas"]), 2)
            },
            aluno2: {
                "notas": aluno2_data["notas"],
                "media_geral": round(sum(aluno2_data["notas"].values()) / len(aluno2_data["notas"]), 2)
            },
            "materias": turma_data["materias"]
        }
        return comparison_data, 200
    except Exception as e:
        logger.error(f"Erro ao comparar alunos na turma {turma_name}: {str(e)}")
        return {"error": f"Erro ao comparar alunos: {str(e)}"}, 500

def compare_students_between_turmas(turma1, aluno1, turma2, aluno2):
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        turmas = grades_data.get("turmas", [])
        turma1_data = next((t for t in turmas if t["nome"] == turma1), None)
        turma2_data = next((t for t in turmas if t["nome"] == turma2), None)
        if not turma1_data or not turma2_data:
            return {"error": f"Uma ou ambas as turmas ({turma1}, {turma2}) não encontradas"}, 404
        aluno1_data = next((a for a in turma1_data["alunos"] if a["nome"] == aluno1), None)
        aluno2_data = next((a for a in turma2_data["alunos"] if a["nome"] == aluno2), None)
        if not aluno1_data or not aluno2_data:
            return {"error": f"Um ou ambos os alunos ({aluno1}, {aluno2}) não encontrados"}, 404
        comparison_data = {
            turma1: {
                "aluno": aluno1,
                "notas": aluno1_data["notas"],
                "media_geral": round(sum(aluno1_data["notas"].values()) / len(aluno1_data["notas"]), 2)
            },
            turma2: {
                "aluno": aluno2,
                "notas": aluno2_data["notas"],
                "media_geral": round(sum(aluno2_data["notas"].values()) / len(aluno2_data["notas"]), 2)
            },
            "materias": turma1_data["materias"]
        }
        return comparison_data, 200
    except Exception as e:
        logger.error(f"Erro ao comparar alunos entre turmas: {str(e)}")
        return {"error": f"Erro ao comparar alunos: {str(e)}"}, 500

def get_students_by_professor(professor_name):
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        professors = grades_data.get("professores", [])
        prof_data = next((p for p in professors if p["nome"] == professor_name), None)
        if not prof_data:
            return {"error": f"Professor {professor_name} não encontrado"}, 404
        turmas = grades_data.get("turmas", [])
        students_by_turma = {}
        for turma_name in prof_data["turmas"]:
            turma_data = next((t for t in turmas if t["nome"] == turma_name), None)
            if turma_data:
                students = [
                    {"nome": aluno["nome"], "notas": aluno["notas"], "media_geral": round(sum(aluno["notas"].values()) / len(aluno["notas"]), 2)}
                    for aluno in turma_data["alunos"]
                ]
                students_by_turma[turma_name] = {"alunos": students, "materias": turma_data["materias"]}
        return {
            "professor": professor_name,
            "materia": prof_data["materia"],
            "nota_professor": prof_data["nota"],
            "turmas": students_by_turma
        }, 200
    except Exception as e:
        logger.error(f"Erro ao listar alunos do professor {professor_name}: {str(e)}")
        return {"error": f"Erro ao listar alunos: {str(e)}"}, 500

def get_initial_comparison_data():
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        all_students = []
        for turma in grades_data.get("turmas", []):
            for aluno in turma.get("alunos", []):
                media_geral = sum(aluno["notas"].values()) / len(aluno["notas"])
                all_students.append({
                    "nome": aluno["nome"],
                    "turma": turma["nome"],
                    "media_geral": round(media_geral, 2)
                })
        top_students = sorted(all_students, key=lambda x: x["media_geral"], reverse=True)[:5]
        materias = grades_data.get("turmas", [])[0].get("materias", [])
        materia_averages = {materia: [] for materia in materias}
        for turma in grades_data.get("turmas", []):
            for aluno in turma.get("alunos", []):
                for materia, nota in aluno["notas"].items():
                    materia_averages[materia].append(nota)
        materia_stats = {
            materia: round(sum(notas) / len(notas), 2)
            for materia, notas in materia_averages.items() if notas
        }
        top_professors = sorted(
            grades_data.get("professores", []),
            key=lambda x: x["nota"],
            reverse=True
        )[:5]
        top_professors = [
            {
                "nome": prof["nome"],
                "materia": prof["materia"],
                "nota": round(prof["nota"], 2),
                "turmas": prof["turmas"]
            }
            for prof in top_professors
        ]
        return {
            "top_students": top_students,
            "materia_stats": materia_stats,
            "top_professors": top_professors
        }, 200
    except Exception as e:
        logger.error(f"Erro ao obter dados iniciais: {str(e)}", exc_info=True)
        return {"error": f"Erro ao obter dados iniciais: {str(e)}"}, 500

def load_new_grades_data():
    try:
        with open(NEW_GRADES_FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": "Arquivo new_grades.json não encontrado"}, 404
    except json.JSONDecodeError as e:
        return {"error": f"Erro ao decodificar new_grades.json: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Erro ao carregar new_grades.json: {str(e)}"}, 500

def get_turmas_list():
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        turmas = [turma["nome"] for turma in grades_data.get("turmas", [])]
        return {"turmas": turmas}, 200
    except Exception as e:
        return {"error": f"Erro ao listar turmas: {str(e)}"}, 500

def compare_classes(turma1, turma2):
    grades_data = load_new_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        turmas = grades_data.get("turmas", [])
        turma1_data = next((t for t in turmas if t["nome"] == turma1), None)
        turma2_data = next((t for t in turmas if t["nome"] == turma2), None)
        if not turma1_data or not turma2_data:
            return {"error": f"Uma ou ambas as turmas ({turma1}, {turma2}) não encontradas"}, 404
        materias = turma1_data["materias"]
        comparison_data = {
            turma1: {"materias": {}, "student_count": len(turma1_data["alunos"]), "average_grade": 0},
            turma2: {"materias": {}, "student_count": len(turma2_data["alunos"]), "average_grade": 0},
            "materias": materias,
        }
        turma1_materias_totals = {materia: [] for materia in materias}
        for aluno in turma1_data["alunos"]:
            for materia in materias:
                turma1_materias_totals[materia].append(aluno["notas"][materia])
        for materia in materias:
            comparison_data[turma1]["materias"][materia] = (
                sum(turma1_materias_totals[materia]) / len(turma1_materias_totals[materia])
                if turma1_materias_totals[materia] else 0
            )
        turma1_avg = sum(comparison_data[turma1]["materias"].values()) / len(materias)
        comparison_data[turma1]["average_grade"] = turma1_avg
        turma2_materias_totals = {materia: [] for materia in materias}
        for aluno in turma2_data["alunos"]:
            for materia in materias:
                turma2_materias_totals[materia].append(aluno["notas"][materia])
        for materia in materias:
            comparison_data[turma2]["materias"][materia] = (
                sum(turma2_materias_totals[materia]) / len(turma2_materias_totals[materia])
                if turma2_materias_totals[materia] else 0
            )
        turma2_avg = sum(comparison_data[turma2]["materias"].values()) / len(materias)
        comparison_data[turma2]["average_grade"] = turma2_avg
        return comparison_data, 200
    except Exception as e:
        return {"error": f"Erro ao comparar turmas: {str(e)}"}, 500

def generate_study_resources(student_email, course_name):
    try:
        if '@' not in student_email:
            return {"error": "Formato de email inválido"}, 400
        username = student_email.split('@')[0]
        course = next((c for c in COURSES if c['course_name'] == course_name), None)
        if not course:
            return {"error": f"Curso {course_name} não encontrado"}, 404
        grades_result, status_code = get_student_grades_by_username(username)
        if status_code != 200:
            return grades_result, status_code
        grades = grades_result.get("grades", [])
        course_grade = next((g for g in grades if g["course_name"] == course_name), None)
        performance = course_grade.get("calculated_grade", 0) if course_grade else 0
        weak_sections = [
            section["subsection_name"] or section["label"]
            for section in course_grade.get("section_breakdown", [])
            if section.get("percent", 0) < 0.7
        ] if course_grade else []
        prompt = f"""
        Sugira recursos de estudo personalizados para o estudante com username '{username}' no curso '{course_name}'.
        O estudante tem uma nota de {performance}%.
        Concentre-se nas áreas fracas: {', '.join(weak_sections) if weak_sections else 'Nenhuma'}.
        Recomende materiais como livros, vídeos, exercícios práticos e links úteis.
        Forneça a resposta em português (Brasil), formatada em texto simples com seções claras:
        ## Recursos de Estudo Personalizados
        ### Curso: {course_name}
        ### Áreas de Foco: {', '.join(weak_sections) if weak_sections else 'Geral'}
        - **Recurso 1**: [Descrição e link]
        - **Recurso 2**: [Descrição e link]
        ...
        """
        try:
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            response = session.post(
                API_BASE_URL,
                json={
                    "messages": [
                        {"role": "system", "content": "Você é um assistente educacional especializado em recomendar recursos de estudo em português (Brasil)."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True,
                    "temperature": 0.55
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            return {
                "student_email": student_email,
                "username": username,
                "course_name": course_name,
                "resources": generate()
            }, 200
        except Exception as e:
            logger.error(f"Failed to generate resources: {str(e)}")
            return {
                "student_email": student_email,
                "username": username,
                "course_name": course_name,
                "resources": None,
                "error": f"Erro ao gerar recursos: {str(e)}"
            }, 500
    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500

def generate_study_plan_student(student_email):
    import logging
    logger = logging.getLogger(__name__)
    try:
        from django.http import request
        data = request.get_json()  # Adjust for Django
        logger.debug(f"Received JSON data: {data}")
        course_name = data.get('course_name')
        theory_minutes = data.get('theory_minutes')
        practice_minutes = data.get('practice_minutes')
        exercise_minutes = data.get('exercise_minutes')
        performance = data.get('grade', 'N/A')
        if not all([course_name, theory_minutes, practice_minutes, exercise_minutes]):
            logger.error("Missing required parameters")
            return {"error": "Parâmetros obrigatórios ausentes: course_name, theory_minutes, practice_minutes, exercise_minutes"}, 400
        if '@' not in student_email:
            logger.error("Invalid email format")
            return {"error": "Formato de email inválido"}, 400
        username = student_email.split('@')[0]
        course = next((c for c in COURSES if c['course_name'] == course_name), None)
        if not course:
            logger.error(f"Course {course_name} not found")
            return {"error": f"Curso {course_name} não encontrado"}, 404
        grades_result, status_code = get_student_grades_by_username(username)
        if status_code != 200:
            logger.error(f"Failed to fetch grades: {grades_result}")
            return grades_result, status_code
        grades = grades_result.get("grades", [])
        course_grade = next((g for g in grades if g["course_name"] == course_name), None)
        weak_sections = [
            section["subsection_name"] or section["label"]
            for section in course_grade.get("section_breakdown", [])
            if section.get("percent", 0) < 0.7
        ] if course_grade else []
        prompt = f"""
        Crie um plano de estudo semanal envolvente para o estudante com username '{username}' no curso '{course_name}'.
        O estudante tem uma nota de {performance}%.
        Concentre-se nas áreas fracas: {', '.join(weak_sections) if weak_sections else 'Nenhuma'}.
        Divida o plano em partes com os seguintes tempos: Teoria: {theory_minutes} min, Prática: {practice_minutes} min, Exercícios: {exercise_minutes} min.
        Inclua objetivos claros, horários sugeridos, dicas práticas para engajar o estudante, e atividades específicas para cada parte.
        Formate o plano em texto simples, com seções claras:
        ## Plano de Estudo Semanal
        ### Curso: {course_name}
        ### Objetivos
        - [Objetivo 1]
        - [Objetivo 2]
        ### Teoria ({theory_minutes} min)
        - [Atividade 1]
        - [Atividade 2]
        ### Prática ({practice_minutes} min)
        - [Atividade 1]
        - [Atividade 2]
        ### Exercícios ({exercise_minutes} min)
        - [Atividade 1]
        - [Atividade 2]
        Forneça a resposta em português (Brasil).
        """
        logger.debug(f"Sending prompt to API: {prompt[:200]}...")
        try:
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            response = session.post(
                API_BASE_URL,
                json={
                    "messages": [
                        {"role": "system", "content": "Você é um assistente educacional especializado em criar planos de estudo personalizados em português (Brasil)."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True,
                    "temperature": 0.55
                },
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        yield decoded_chunk
                yield "\n[DONE]\n"
            return StreamingHttpResponse(generate(), content_type='text/plain; charset=utf-8')
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {"error": f"Erro ao gerar plano: {str(e)}"}, 500
    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500

def get_student_grades_by_username(username):
    grades_data = load_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        grades_list = []
        username_lower = username.lower()
        for course_id, course_data in grades_data.items():
            course_name = course_data.get("course_name", course_id)
            for grade in course_data.get("grades", []):
                if grade.get("username", "").lower() == username_lower:
                    grades_list.append({
                        "course_id": course_id,
                        "course_name": course_name,
                        "calculated_grade": grade.get("calculated_grade", 0.0),
                        "section_breakdown": grade.get("section_breakdown", []),
                        "user_id": grade.get("user_id"),
                        "username": grade.get("username"),
                        "email": grade.get("email", "")
                    })
        if not grades_list:
            return {"error": f"Nenhuma nota encontrada para o aluno {username}"}, 404
        return {
            "username": username,
            "grades": grades_list
        }, 200
    except Exception as e:
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_access_token():
    token_url = f"{BASE_URL}/oauth2/access_token/"
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": USERNAME,
        "password": PASSWORD,
        "scope": "read write"
    }
    try:
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    except Exception as e:
        return {"error": f"Erro ao obter token: {str(e)}"}, 500

def handle_chat_message(message, study_mode, course_id=None, user_id=None):
    system_prompt = {
        "Estudo": "Você é um assistente eficiente que ajuda alunos com dúvidas gerais.",
        "Direcionamento": "Você é um assistente especializado em direcionar estudos para alunos.",
        "Professor": "Você é um assistente para professores, ajude a criar atividades e fornecer feedbacks."
    }.get(study_mode, "Você é um assistente útil.")
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.post(
            API_BASE_URL,
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.55
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return {
            "success": True,
            "message": data['choices'][0]['message']['content'],
            "course_id": course_id
        }
    except Exception as e:
        logger.error(f"Chat message processing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def get_course_content(course_id, chapter, section):
    course = next((c for c in COURSES if c['course_id'] == course_id), None)
    if not course:
        return {"error": "Curso não encontrado"}, 404
    url = f"{settings.FILE_SERVER_BASE_URL}/{course['server']}/Capitulo{chapter}/{section}/index.html"
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return {
            "course_id": course_id,
            "chapter": chapter,
            "section": section,
            "content": text,
            "url": url
        }
    except Exception as e:
        logger.error(f"Failed to fetch course content: {str(e)}")
        return {"error": str(e)}, 500

def load_grades_data():
    try:
        with open(GRADES_FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": "Arquivo all_grades.json não encontrado"}, 404
    except json.JSONDecodeError as e:
        return {"error": f"Erro ao decodificar all_grades.json: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Erro ao carregar all_grades.json: {str(e)}"}, 500

def get_student_grades(student_id):
    grades_data = load_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    grades_result = []
    try:
        student_id = int(student_id)
        for course_id, course_data in grades_data.items():
            course_name = course_data.get("course_name", course_id)
            for grade in course_data.get("grades", []):
                if grade.get("user_id") == student_id:
                    grades_result.append({
                        "course_id": course_id,
                        "course_name": course_name,
                        "calculated_grade": grade.get("calculated_grade"),
                        "section_breakdown": grade.get("section_breakdown", [])
                    })
        return {
            "student_id": student_id,
            "grades": grades_result
        }, 200
    except ValueError:
        return {"error": "ID do aluno inválido"}, 400
    except Exception as e:
        logger.error(f"Failed to fetch student grades: {str(e)}")
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_specific_student_grade(student_email, course_id):
    grades_data = load_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    try:
        course_data = grades_data.get(course_id)
        if not course_data:
            return {"error": f"Curso {course_id} não encontrado"}, 404
        for grade in course_data.get("grades", []):
            if grade.get("email", "").lower() == student_email.lower():
                return {
                    "student_email": student_email,
                    "course_id": course_id,
                    "course_name": course_data.get("course_name"),
                    "grade": grade.get("calculated_grade"),
                    "section_breakdown": grade.get("section_breakdown", [])
                }, 200
        return {
            "student_email": student_email,
            "course_id": course_id,
            "grades": [],
            "section_breakdown": []
        }, 200
    except Exception as e:
        logger.error(f"Failed to fetch specific student grade: {str(e)}")
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_student_grades_all_courses(student_email):
    grades_data = load_grades_data()
    if isinstance(grades_data, dict) and "error" in grades_data:
        return grades_data, grades_data.get("status", 500)
    grades_list = []
    try:
        for course_id, course_data in grades_data.items():
            course_name = course_data.get("course_name", course_id)
            found = False
            for grade in course_data.get("grades", []):
                if grade.get("email", "").lower() == student_email.lower():
                    grades_list.append({
                        "course_id": course_id,
                        "course_name": course_name,
                        "calculated_grade": grade.get("calculated_grade"),
                        "section_breakdown": grade.get("section_breakdown", []),
                        "user_id": grade.get("user_id"),
                        "username": grade.get("username"),
                        "email": grade.get("email")
                    })
                    found = True
                    break
            if not found:
                grades_list.append({
                    "course_id": course_id,
                    "course_name": course_name,
                    "calculated_grade": 0,
                    "section_breakdown": [],
                    "user_id": None,
                    "username": None,
                    "email": student_email
                })
        return {
            "student_email": student_email,
            "grades": grades_list
        }, 200
    except Exception as e:
        logger.error(f"Failed to fetch all student grades: {str(e)}")
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_all_student_grades():
    def generate():
        grades_data = load_grades_data()
        if isinstance(grades_data, dict) and "error" in grades_data:
            yield json.dumps({"type": "error", "error": grades_data['error']}) + '\n'
            return
        try:
            total_courses = len(grades_data)
            yield json.dumps({"type": "summary", "total_courses": total_courses}) + '\n'
            for course_id, course_data in grades_data.items():
                course_name = course_data.get("course_name", course_id)
                grades_count = len(course_data.get("grades", []))
                logger.debug(f"Processing course {course_id} with {grades_count} grades")
                yield json.dumps({
                    "type": "course_start",
                    "course_id": course_id,
                    "course_name": course_name,
                    "total_students": grades_count
                }) + '\n'
                for grade in course_data.get("grades", []):
                    logger.debug(f"Processing grade for {grade.get('username')} in {course_id}")
                    try:
                        processed_grade = {
                            "user_id": grade.get("user_id"),
                            "username": grade.get("username"),
                            "email": grade.get("email", ""),
                            "calculated_grade": grade.get("calculated_grade", 0.0),
                            "section_breakdown": grade.get("section_breakdown", [])
                        }
                        yield json.dumps({
                            "type": "grade",
                            "course_id": course_id,
                            "course_name": course_name,
                            "grade": processed_grade
                        }) + '\n'
                    except Exception as e:
                        logger.error(f"Error processing grade for {grade.get('username')} in {course_id}: {str(e)}")
                        yield json.dumps({
                            "type": "error",
                            "course_id": course_id,
                            "username": grade.get("username"),
                            "error": f"Erro ao processar nota: {str(e)}"
                        }) + '\n'
                yield json.dumps({
                    "type": "course_end",
                    "course_id": course_id,
                    "course_name": course_name
                }) + '\n'
        except Exception as e:
            logger.error(f"General error in get_all_student_grades: {str(e)}")
            yield json.dumps({"type": "error", "error": f"Erro geral ao buscar notas: {str(e)}"}) + '\n'
    return generate

def compare_cities():
    def generate():
        grades_data = load_grades_data()
        if isinstance(grades_data, dict) and "error" in grades_data:
            yield json.dumps({"type": "error", "error": grades_data['error']}) + '\n'
            return
        try:
            total_courses = len(grades_data)
            logger.debug(f"Total courses in all_grades.json: {total_courses}")
            yield json.dumps({"type": "summary", "total_courses": total_courses}) + '\n'
            expected_courses = [
                "course-v1:Projeto_Desenvolve+PY001+2024_S2",
                "course-v1:ProjetoDesenvolve+Scratch1+01",
                "course-v1:ProjetoDesenvolve+NoCode1+01",
                "course-v1:ProjetoDesenvolve+Linux1+01",
                "course-v1:ProjetoDesenvolve+IntroWeb+01",
                "course-v1:ProjetoDesenvolve+POO1+01",
                "course-v1:ProjetoDesenvolve+JS1+01",
                "course-v1:ProjetoDesenvolve+BD1+01",
                "course-v1:ProjetoDesenvolve+Python2+2024",
                "course-v1:ProjetoDesenvolve+Projeto1+01",
                "course-v1:ProjetoDesenvolve+Projeto2+01"
            ]
            logger.debug(f"Expected courses: {expected_courses}")
            comparison_data = {"Itabira": {}, "Bom_Despacho": {}}
            processed_courses = set()
            for course_id, course_data in grades_data.items():
                course_name = course_data.get("course_name", course_id)
                logger.debug(f"Processing course: {course_id} ({course_name})")
                processed_courses.add(course_id)
                yield json.dumps({
                    "type": "course_start",
                    "course_id": course_id,
                    "course_name": course_name,
                    "total_students": len(course_data.get("grades", []))
                }) + '\n'
                itabira_grades = []
                bom_despacho_grades = []
                itabira_completions = []
                bom_despacho_completions = []
                itabira_students = set()
                bom_despacho_students = set()
                grades_count = len(course_data.get("grades", []))
                logger.debug(f"Total students in {course_id}: {grades_count}")
                if grades_count == 0:
                    logger.debug(f"No grades found for course {course_id}")
                for grade in course_data.get("grades", []):
                    username = grade.get("username", "").lower()
                    user_id = grade.get("user_id", 0)
                    calculated_grade = grade.get("calculated_grade", 0.0)
                    section_breakdown = grade.get("section_breakdown", [])
                    total_activities = len(section_breakdown)
                    attempted_activities = sum(1 for section in section_breakdown if section.get("attempted", False))
                    completion_rate = (attempted_activities / total_activities * 100) if total_activities > 0 else 0
                    if "pdita" in username:
                        city = "Itabira"
                        itabira_grades.append(calculated_grade)
                        itabira_completions.append(completion_rate)
                        itabira_students.add(user_id)
                        logger.debug(f"Itabira student: {username}, grade: {calculated_grade}")
                    elif "pdbd" in username:
                        city = "Bom Despacho"
                        bom_despacho_grades.append(calculated_grade)
                        bom_despacho_completions.append(completion_rate)
                        bom_despacho_students.add(user_id)
                        logger.debug(f"Bom Despacho student: {username}, grade: {calculated_grade}")
                    else:
                        city = "Itabira" if user_id % 2 else "Bom Despacho"
                        if city == "Itabira":
                            itabira_grades.append(calculated_grade)
                            itabira_completions.append(completion_rate)
                            itabira_students.add(user_id)
                        else:
                            bom_despacho_grades.append(calculated_grade)
                            bom_despacho_completions.append(completion_rate)
                            bom_despacho_students.add(user_id)
                        logger.debug(f"Assigned {username} to {city}, grade: {calculated_grade}")
                comparison_data["Itabira"][course_id] = {
                    "course_name": course_name,
                    "average_grade": round(sum(itabira_grades) / len(itabira_grades), 2) if itabira_grades else 0,
                    "student_count": len(itabira_students),
                    "average_completion_rate": round(sum(itabira_completions) / len(itabira_completions), 2) if itabira_completions else 0
                }
                comparison_data["Bom_Despacho"][course_id] = {
                    "course_name": course_name,
                    "average_grade": round(sum(bom_despacho_grades) / len(bom_despacho_grades), 2) if bom_despacho_grades else 0,
                    "student_count": len(bom_despacho_students),
                    "average_completion_rate": round(sum(bom_despacho_completions) / len(bom_despacho_completions), 2) if bom_despacho_completions else 0
                }
                logger.debug(f"Course {course_id} summary: Itabira students={len(itabira_students)}, Bom Despacho students={len(bom_despacho_students)}")
                yield json.dumps({
                    "type": "course_data",
                    "course_id": course_id,
                    "itabira": comparison_data["Itabira"][course_id],
                    "bom_despacho": comparison_data["Bom_Despacho"][course_id]
                }) + '\n'
                yield json.dumps({
                    "type": "course_end",
                    "course_id": course_id,
                    "course_name": course_name
                }) + '\n'
            for course_id in expected_courses:
                if course_id not in processed_courses:
                    logger.debug(f"Adding missing course: {course_id}")
                    course_name = next((c["course_name"] for c in [
                        {"course_id": "course-v1:Projeto_Desenvolve+PY001+2024_S2", "course_name": "Python 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+Scratch1+01", "course_name": "Scratch 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+NoCode1+01", "course_name": "No Code 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+Linux1+01", "course_name": "Linux 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+IntroWeb+01", "course_name": "Introdução à Web"},
                        {"course_id": "course-v1:ProjetoDesenvolve+POO1+01", "course_name": "Programação Orientada a Objetos (POO) 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+JS1+01", "course_name": "JavaScript 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+BD1+01", "course_name": "Banco de Dados 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+Python2+2024", "course_name": "Python 2"},
                        {"course_id": "course-v1:ProjetoDesenvolve+Projeto1+01", "course_name": "Projeto 1"},
                        {"course_id": "course-v1:ProjetoDesenvolve+Projeto2+01", "course_name": "Projeto 2"}
                    ] if c["course_id"] == course_id), course_id)
                    comparison_data["Itabira"][course_id] = {
                        "course_name": course_name,
                        "average_grade": 0,
                        "student_count": 0,
                        "average_completion_rate": 0
                    }
                    comparison_data["Bom_Despacho"][course_id] = {
                        "course_name": course_name,
                        "average_grade": 0,
                        "student_count": 0,
                        "average_completion_rate": 0
                    }
                    yield json.dumps({
                        "type": "course_data",
                        "course_id": course_id,
                        "itabira": comparison_data["Itabira"][course_id],
                        "bom_despacho": comparison_data["Bom_Despacho"][course_id]
                    }) + '\n'
            yield json.dumps({"type": "complete", "data": comparison_data}) + '\n'
        except Exception as e:
            logger.error(f"Error in compare_cities: {str(e)}")
            yield json.dumps({"type": "error", "error": f"Erro ao comparar cidades: {str(e)}"}) + '\n'
    return generate

def generate_study_plan(student_id, course_id, weak_subjects):
    plan_prompt = f"""
    Crie um plano de estudo semanal para o aluno {student_id} no curso {course_id},
    focando especialmente em: {', '.join(weak_subjects)}.
    Inclua tópicos diários, recursos recomendados e exercícios práticos.
    """
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.post(
            API_BASE_URL,
            json={
                "messages": [
                    {"role": "system", "content": "Você é um tutor especializado em criar planos de estudo personalizados."},
                    {"role": "user", "content": plan_prompt}
                ],
                "temperature": 0.4
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return {
            "student_id": student_id,
            "course_id": course_id,
            "plan": data['choices'][0]['message']['content']
        }
    except Exception as e:
        logger.error(f"Failed to generate study plan: {str(e)}")
        return {"error": str(e)}, 500

def generate_teaching_materials(teacher_id, course_id, material_type):
    material_prompts = {
        "resumo": "Crie um resumo claro e conciso dos tópicos principais",
        "exercicios": "Sugira exercícios práticos for para os alunos",
        "plano_aula": "Elabore um plano de aula detalhado",
        "recursos": "Recomende recursos didáticos adicionais"
    }
    if material_type not in material_prompts:
        return {"error": "Tipo de material inválido"}, 400
    prompt = f"""
    {material_prompts[material_type]} para o curso {course_id}.
    O material deve ser adequado para o nível dos alunos e alinhado com o currículo.
    """
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.post(
            API_BASE_URL,
            json={
                "messages": [
                    {"role": "system", "content": "Você é um assistente para professores, especializado em criação de materiais didáticos."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return {
            "teacher_id": teacher_id,
            "course_id": course_id,
            "material_type": material_type,
            "content": data['choices'][0]['message']['content']
        }
    except Exception as e:
        logger.error(f"Failed to generate teaching materials: {str(e)}")
        return {"error": str(e)}, 500

def get_student_grades_by_email(email):
    try:
        if '@' not in email:
            return {"error": "Email inválido: formato incorreto"}, 400
        username = email.split('@')[0]
        return get_student_grades_by_username(username)
    except Exception as e:
        logger.error(f"Failed to process email: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500

def generate_simulado(student_email, mode='weak', course_id=None):
    try:
        if '@' not in student_email:
            logger.error("Invalid email format")
            return {"error": "Email inválido: formato incorreto"}, 400
        username = student_email.split('@')[0]
        logger.debug(f"Generating simulado for username: {username}, mode: {mode}, course_id: {course_id}")
        grades_result, status_code = get_student_grades_by_username(username)
        if status_code != 200:
            logger.error(f"Failed to fetch grades: {grades_result}")
            return grades_result, status_code
        grades = grades_result.get("grades", [])
        target_areas = []
        threshold = 70
        condition = lambda x: x < threshold if mode == 'weak' else x >= threshold
        description = 'áreas com notas abaixo de 70%' if mode == 'weak' else 'áreas com notas de 70% ou acima'
        for grade in grades:
            if course_id and grade["course_id"] != course_id:
                continue
            if condition(grade.get("calculated_grade", 0)):
                target_sections = [
                    section["subsection_name"] or section["label"]
                    for section in grade.get("section_breakdown", [])
                    if condition(section.get("percent", 0) * 100)
                ]
                if target_sections:
                    target_areas.append({
                        "course_id": grade["course_id"],
                        "course_name": grade["course_name"],
                        "calculated_grade": grade.get("calculated_grade", 0),
                        "target_sections": target_sections
                    })
        logger.debug(f"Target areas: {json.dumps(target_areas, indent=2)}")
        if not target_areas:
            logger.info(f"No {description} found for simulado generation")
            return {
                "student_email": student_email,
                "username": username,
                "grades": grades,
                "simulado": None,
                "message": f"Nenhuma {description} encontrada para gerar simulado."
            }, 200
        simulado_prompt = f"""
        Crie um simulado profissional com **10 questões** para o aluno com username {username}.
        Baseie-se nas seguintes {description}:
        {json.dumps([{
            "course_name": area["course_name"],
            "target_sections": area["target_sections"]
        } for area in target_areas], indent=2, ensure_ascii=False)}.
        As questões devem ser distribuídas entre os cursos listados, com uma mistura de **múltipla escolha** (7 questões) e **dissertativas** (3 questões).
        Cada questão deve incluir:
        - **Enunciado claro** relacionado ao curso e seção.
        - **Tipo** (múltipla escolha ou dissertativa).
        - **Objetivo** (o que a questão avalia).
        - **Nível de dificuldade** (fácil, médio, difícil).
        - Para múltipla escolha: **4 opções**, com **1 correta** claramente indicada.
        Formate em texto simples com seções claras:
        ## Simulado Personalizado
        ### Instruções
        - Responda todas as questões.
        - Para múltipla escolha, selecione a opção correta.
        - Para dissertativas, forneça uma resposta completa.
        ## Questão 1
        ### Curso: [Curso]
        ### Seção: [Seção]
        ### Objetivo: [Objetivo]
        ### Tipo: [Múltipla Escolha/Dissertativa]
        ### Dificuldade: [Fácil/Médio/Difícil]
        ### Enunciado: [Enunciado]
        ### Opções (se múltipla escolha):
        - A) [Opção A]
        - B) [Opção B]
        - C) [Opção C]
        - D) [Opção D]
        ### Resposta Correta (se múltipla escolha): [Letra]
        Assegure que as questões sejam variadas e cubram diferentes tópicos dos cursos indicados.
        Forneça a resposta em português (Brasil).
        """
        logger.debug(f"Simulado prompt (first 200 chars): {simulado_prompt[:200]}...")
        try:
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            response = session.post(
                API_BASE_URL,
                json={
                    "messages": [
                        {"role": "system", "content": "Você é um assistente educacional especializado em criar simulados personalizados para alunos."},
                        {"role": "user", "content": simulado_prompt}
                    ],
                    "stream": True,
                    "temperature": 0.55
                },
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        logger.debug(f"Received chunk: {decoded_chunk[:100]}...")
                        yield decoded_chunk
                yield "\n[DONE]\n"
            return {
                "student_email": student_email,
                "username": username,
                "grades": grades,
                "simulado": generate()
            }, 200
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {
                "student_email": student_email,
                "username": username,
                "grades": grades,
                "simulado": None,
                "error": f"Erro ao gerar simulado: {str(e)}",
                "message": "Não foi possível gerar o simulado devido a um problema de conexão com o servidor. Tente novamente mais tarde."
            }, 500
    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500
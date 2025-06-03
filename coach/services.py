import requests
from bs4 import BeautifulSoup
from django.conf import settings
import os
import json
import logging
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
BASE_URL = "https://projetodesenvolve.online"
CLIENT_ID = os.getenv("CLIENT_ID", "mycoach-consumer")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "0vpaOnw1lzL0iaGSEcGjkUusclqHscYkWPrH1tA9fU48AvX0C9eeWO1iy2Yi3wwjdUilrAQzT3PyXbC2qW2s8rDINDo6dnpNDv2ZiXlGHOjRMp2AuzG8BAmHtpeX0Orb")
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "X58cN20jI3qM")
GRADES_FILE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'all_grades.json')

# Load courses from cursos.json
try:
    with open(os.path.join(os.path.dirname(__file__), 'data', 'cursos.json'), 'r') as file:
        COURSES = json.load(file)
except FileNotFoundError:
    raise ImproperlyConfigured("cursos.json not found")

def generate_study_resources(student_email, course_name):
    """
    Gera recursos de estudo personalizados para um estudante em um curso específico.
    """
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

        try:
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
            ```
            ## Recursos de Estudo Personalizados
            ### Curso: {course_name}
            ### Áreas de Foco: {', '.join(weak_sections) if weak_sections else 'Geral'}
            - **Recurso 1**: [Descrição e link]
            - **Recurso 2**: [Descrição e link]
            ...
            ```
            """
            
            response = requests.post(
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
                timeout=10
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
            logger.error(f"Erro ao processar recursos: {str(e)}")
            return {
                "student_email": student_email,
                "username": username,
                "course_name": course_name,
                "resources": None,
                "error": f"Erro ao gerar recursos: {str(e)}"
            }, 500
    except Exception as e:
        logger.error(f"Erro ao processar email: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500

def generate_study_plan_student(student_email, data):
    """
    Gera um plano de estudo semanal para um estudante em um curso específico.
    """
    try:
        course_name = data.get('course_name')
        theory_minutes = data.get('theory_minutes')
        practice_minutes = data.get('practice_minutes')
        exercise_minutes = data.get('exercise_minutes')
        performance = data.get('grade', 0)

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

        try:
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
            Inclua tópicos diários, recursos recomendados e exercícios práticos.
            Forneça a resposta em português (Brasil), formatada em texto simples com seções claras:
            ```
            ## Plano de Estudo Semanal
            ### Curso: {course_name}
            ### Segunda-feira
            - **Tópico**: [Tópico]
            - **Recursos**: [Recursos]
            - **Exercícios**: [Exercícios]
            ### Terça-feira
            ...
            ```
            """
            logger.debug(f"Sending prompt to API: {prompt[:200]}...")

            response = requests.post(
                API_BASE_URL,
                json={
                    "messages": [
                        {"role": "system", "content": "Você é um tutor especializado em criar planos de estudo personalizados em português (Brasil)."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True,
                    "temperature": 0.4
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()

            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        logger.debug(f"Received chunk: {decoded_chunk[:100]}...")
                        yield decoded_chunk

            return {
                "student_email": student_email,
                "username": username,
                "course_name": course_name,
                "plan": generate()
            }, 200
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return {"error": f"Erro ao processar plano: {str(e)}"}, 500
    except Exception as e:
        logger.error(f"Email processing error: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500

def get_student_grades_by_username(username):
    """
    Obtém as notas de um aluno com base no username.
    """
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
        logger.error(f"Erro ao buscar notas: {str(e)}")
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_access_token():
    """
    Obtém um token de acesso para a API.
    """
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
        logger.error(f"Erro ao obter token: {str(e)}")
        return {"error": f"Erro ao obter token: {str(e)}"}, 500

def handle_chat_message(message, study_mode, course_id=None, user_id=None):
    """
    Processa mensagens do chat com base no modo de estudo.
    """
    system_prompt = {
        "Estudo": "Você é um assistente eficiente que ajuda alunos com dúvidas gerais.",
        "Direcionamento": "Você é um assistente especializado em direcionar estudos para alunos.",
        "Professor": "Você é um assistente para professores, ajude a criar atividades e fornecer feedbacks."
    }.get(study_mode, "Você é um assistente útil.")
    
    try:
        response = requests.post(
            API_BASE_URL,
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.55
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "message": data['choices'][0]['message']['content'],
            "course_id": course_id
        }
    except Exception as e:
        logger.error(f"Erro ao processar mensagem de chat: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def get_course_content(course_id, chapter, section):
    """
    Obtém conteúdo do curso do servidor de arquivos.
    """
    course = next((c for c in settings.COURSES if c['course_id'] == course_id), None)
    if not course:
        return {"error": "Curso não encontrado"}, 404
    
    url = f"{settings.FILE_SERVER_BASE_URL}/{course['server']}/Capitulo{chapter}/{section}/index.html"
    
    try:
        response = requests.get(url, timeout=10)
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
        logger.error(f"Erro ao obter conteúdo: {str(e)}")
        return {"error": str(e)}, 500

def load_grades_data():
    """
    Carrega o arquivo all_grades.json.
    """
    try:
        with open(GRADES_FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error("Arquivo all_grades.json não encontrado")
        return {"error": "Arquivo all_grades.json não encontrado"}, 404
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar all_grades.json: {str(e)}")
        return {"error": f"Erro ao decodificar all_grades.json: {str(e)}"}, 500
    except Exception as e:
        logger.error(f"Erro ao carregar all_grades.json: {str(e)}")
        return {"error": f"Erro ao carregar all_grades.json: {str(e)}"}, 500

def get_student_grades(student_id):
    """
    Obtém as notas de um aluno específico em todos os cursos.
    """
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
        logger.error("ID do aluno inválido")
        return {"error": "ID do aluno inválido"}, 400
    except Exception as e:
        logger.error(f"Erro ao buscar notas: {str(e)}")
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_specific_student_grade(student_email, course_id):
    """
    Obtém as notas de um aluno específico em um curso específico.
    """
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
        logger.error(f"Erro ao buscar notas: {str(e)}")
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_student_grades_all_courses(student_email):
    """
    Obtém as notas de um aluno em todos os cursos.
    """
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
        logger.error(f"Erro ao buscar notas: {str(e)}")
        return {"error": f"Erro ao buscar notas: {str(e)}"}, 500

def get_all_student_grades():
    """
    Obtém todas as notas de todos os alunos.
    """
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
    """
    Compara o desempenho entre as cidades Itabira e Bom Despacho.
    """
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
                    elif "pdbd" in username:
                        city = "Bom Despacho"
                        bom_despacho_grades.append(calculated_grade)
                        bom_despacho_completions.append(completion_rate)
                        bom_despacho_students.add(user_id)
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
    """
    Gera um plano de estudo personalizado.
    """
    plan_prompt = f"""
    Crie um plano de estudo semanal para o aluno {student_id} no curso {course_id},
    focando especialmente em: {', '.join(weak_subjects)}.
    Inclua tópicos diários, recursos recomendados e exercícios práticos.
    """
    
    try:
        response = requests.post(
            API_BASE_URL,
            json={
                "messages": [
                    {"role": "system", "content": "Você é um tutor especializado em criar planos de estudo personalizados."},
                    {"role": "user", "content": plan_prompt}
                ],
                "temperature": 0.4
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "student_id": student_id,
            "course_id": course_id,
            "plan": data['choices'][0]['message']['content']
        }
    except Exception as e:
        logger.error(f"Erro ao gerar plano de estudo: {str(e)}")
        return {"error": str(e)}, 500

def generate_teaching_materials(teacher_id, course_id, material_type):
    """
    Gera materiais de ensino para professores.
    """
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
        response = requests.post(
            API_BASE_URL,
            json={
                "messages": [
                    {"role": "system", "content": "Você é um assistente para professores, especializado em criação de materiais didáticos."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            },
            headers={"Content-Type": "application/json"},
            timeout=10
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
        logger.error(f"Erro ao gerar materiais de ensino: {str(e)}")
        return {"error": str(e)}, 500

def get_student_grades_by_email(email):
    """
    Obtém as notas de um aluno com base no email.
    """
    try:
        if '@' not in email:
            return {"error": "Email inválido: formato incorreto"}, 400
        username = email.split('@')[0]
        return get_student_grades_by_username(username)
    except Exception as e:
        logger.error(f"Erro ao processar email: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500

def generate_simulado(student_email, mode='weak', course_id=None):
    """
    Gera um simulado personalizado para um aluno com base nas notas.
    """
    try:
        if '@' not in student_email:
            return {"error": "Email inválido: formato incorreto"}, 400
        username = student_email.split('@')[0]

        grades_result, status_code = get_student_grades_by_username(username)
        if status_code != 200:
            return grades_result, status_code

        try:
            grades = grades_result.get("grades", [])
            target_areas = []
            threshold = 70
            condition = lambda x: x < threshold if mode == 'weak' else x >= threshold
            description = 'áreas com notas abaixo de 70%' if mode == 'weak' else 'áreas com notas de 70% ou acima'

            for grade in grades:
                if course_id and grade["course_id"] != course_id:
                    continue
                if condition(grade.get("calculated_grade", 0)):
                    target_areas.append({
                        "course_id": grade["course_id"],
                        "course_name": grade["course_name"],
                        "calculated_grade": grade.get("calculated_grade", 0),
                        "target_sections": [
                            section["subsection_name"] or section["label"]
                            for section in grade.get("section_breakdown", [])
                            if condition(section.get("percent", 0) * 100)
                        ]
                    })

            if not target_areas:
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
            {json.dumps(target_areas, indent=2)}.
            As questões devem ser distribuídas entre os cursos listados, com uma mistura de **múltipla escolha** (7 questões) e **dissertativas** (3 questões).
            Cada questão deve incluir:
            - **Enunciado claro** relacionado ao curso e seção.
            - **Tipo** (múltipla escolha ou dissertativa).
            - **Objetivo** (o que a questão avalia).
            - **Nível de dificuldade** (fácil, médio, difícil).
            - Para múltipla escolha: **4 opções**, com **1 correta** claramente indicada.
            Formate em texto simples com seções claras:
            ```
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
            ```
            Assegure que as questões sejam variadas e cubram diferentes tópicos dos cursos indicados.
            """
            
            response = requests.post(
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
                timeout=10
            )
            response.raise_for_status()

            def generate():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')

            return {
                "student_email": student_email,
                "username": username,
                "grades": grades,
                "simulado": generate()
            }, 200
        except Exception as e:
            logger.error(f"Erro ao processar simulado: {str(e)}")
            return {
                "student_email": student_email,
                "username": username,
                "grades": grades,
                "simulado": None,
                "error": f"Erro ao gerar simulado: {str(e)}"
            }, 500
    except Exception as e:
        logger.error(f"Erro ao processar email: {str(e)}")
        return {"error": f"Erro ao processar email: {str(e)}"}, 500
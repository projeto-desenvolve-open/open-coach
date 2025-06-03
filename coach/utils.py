from django.http import JsonResponse
from bs4 import BeautifulSoup

def validate_request(request, required_fields):
    """
    Valida os dados da requisição e verifica campos obrigatórios.
    """
    if not request.content_type == 'application/json':
        return JsonResponse({"error": "Request must be JSON"}, status=400)

    try:
        data = request.data
    except AttributeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return JsonResponse({
            "error": "Missing required fields",
            "missing": missing_fields
        }, status=400)

    return data

def extract_text_from_html(html):
    """
    Extrai texto limpo de conteúdo HTML.
    """
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text
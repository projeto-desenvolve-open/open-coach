from services.tasks.email_task import send_email_task
from django.template.loader import render_to_string
from django.conf import settings

class EmailService:
    """
    Classe para envio de e-mails utilizando Celery em background.
    """
    def __init__(self, subject=None, to_email=None, template_name=None, context=None, from_email=None, cc=None, bcc=None, attachments=None):
        self.subject = subject or "Sem Assunto"
        self.to_email = to_email if isinstance(to_email, list) else [to_email]
        self.template_name = template_name
        self.context = self._prepare_context(context)
        self.from_email = from_email or settings.DEFAULT_FROM_EMAIL
        self.cc = cc or []
        self.bcc = bcc or []
        self.attachments = attachments or []

    def _prepare_context(self, context):
        """
        Transforma objetos Django em strings para evitar erro de serialização no Celery.
        """
        if not context:
            return {}

        return {key: str(value) if hasattr(value, '__dict__') else value for key, value in context.items()}

    def send(self):
        """
        Envia o e-mail de forma assíncrona via Celery.
        """
        send_email_task.delay(
            self.subject,
            self.to_email,
            self.template_name,
            self.context,  # Contexto agora serializável
            self.from_email,
            self.cc,
            self.bcc,
            self.attachments
        )
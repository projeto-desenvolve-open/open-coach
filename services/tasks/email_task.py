from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def send_email_task(subject, to_email, template_name, context, from_email=None, cc=None, bcc=None, attachments=None):
    """
    Tarefa Celery para envio de e-mails em background.
    """
    message = render_to_string(template_name, context)
    
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=[to_email] if isinstance(to_email, str) else to_email,
        cc=cc or [],
        bcc=bcc or []
    )
    email.content_subtype = "html"

    if attachments:
        for attachment in attachments:
            email.attach(attachment.get('filename'), attachment.get('content'), attachment.get('mimetype'))

    email.send()
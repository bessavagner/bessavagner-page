import aiosmtplib
from email.message import EmailMessage
from app.settings import (
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_USE_TLS,
    EMAIL_DEFAULT_SENDER,
    TEMPLATES_DIR
)


async def send_email(subject: str, recipients: list, body: str, sender: str = None):
    """
    Sends an email using the SMTP configuration.
    """
    sender = sender or EMAIL_DEFAULT_SENDER

    # Create the email message
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    # Send the email
    await aiosmtplib.send(
        message,
        hostname=EMAIL_HOST,
        port=EMAIL_PORT,
        username=EMAIL_USERNAME,
        password=EMAIL_PASSWORD,
        use_tls=EMAIL_USE_TLS,
    )

async def send_confirmation_email(name: str,
                                  user_email: str,
                                  user_message: str,
                                  sender: str = None):
    subject = "Thank You for Contacting Me!"
    sender = sender or EMAIL_DEFAULT_SENDER
    
    # Prepare the email
    email = EmailMessage()
    email["From"] = sender
    email["To"] = user_email
    email["Subject"] = subject
    
    # Replace placeholders with actual values
    template = ''
    path = TEMPLATES_DIR / "emails" / "contact.html"
    with open(path, "r", encoding="utf-8") as f:
        template = f.read()
    html_content = template.replace(
        "{{ name }}", name
    ).replace("{{ user_message }}", user_message)
    
    # Add the HTML content
    email.add_alternative(html_content, subtype="html")
    
    # Send the email
    await aiosmtplib.send(
        email,
        hostname=EMAIL_HOST,
        port=EMAIL_PORT,
        username=EMAIL_USERNAME,
        password=EMAIL_PASSWORD,
        use_tls=EMAIL_USE_TLS,
    )

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os

def send_email(html_body, email_smtp_server, email_smtp_port, email_password):
    email_sender = os.getenv('email_sender')
    email_recipients = os.getenv('email_recipients', '').split(',')
    if not email_sender:
        raise ValueError("email_sender environment variable is not set.")
    if not email_recipients or email_recipients == ['']:
        raise ValueError("email_recipients environment variable is not set.")

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = ', '.join(email_recipients)
    msg['Subject'] = 'Daily Azure Cost Update'

    # Render the email body
    template = Template(html_body)
    body = template.render()

    msg.attach(MIMEText(body, 'html'))

    if os.getenv('DEBUG', 'false').lower() == 'true':
        print("Email content:")
        print("From:", msg['From'])
        print("To:", msg['To'])
        print("Subject:", msg['Subject'])
        print("Body:")
        print(body)

    # Send the email
    with smtplib.SMTP(email_smtp_server, email_smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        if not email_password:
            raise ValueError("Email password is not set. Please check your environment variables.")
        smtp.login("apikey", email_password)  # Use "apikey" as the login name and the API key as the password
        smtp.send_message(msg)
        print('Email sent successfully using SendGrid.')

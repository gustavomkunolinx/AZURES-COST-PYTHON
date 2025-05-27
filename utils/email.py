import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os

def send_email(html_table_rows, email_smtp_server, email_smtp_port, email_password, label_a="Current", label_b="Previous"):
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
    msg['Subject'] = 'Azure Cost Comparison Report'

    # Create the HTML email body with the comparison table
    html_body = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #0078d4; margin-bottom: 20px; }}
                h2 {{ color: #106ebe; margin-top: 30px; margin-bottom: 15px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th {{ background-color: #0078d4; color: white; padding: 12px; text-align: left; border: 1px solid #ddd; }}
                td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:hover {{ background-color: #e8f4fd; }}
                .increase {{ background-color: #ffcccc !important; }}
                .summary {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                .highlight-note {{ color: #d13438; font-weight: bold; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>Azure Cost Comparison Report</h1>

            <div class="summary">
                <h2>Cost Comparison: {label_a} vs {label_b}</h2>
                <p>This report shows the cost comparison between two periods for your Azure services.</p>
            </div>

            <h2>Service Cost Comparison</h2>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>{label_a}</th>
                        <th>{label_b}</th>
                        <th>Difference (R$)</th>
                        <th>Difference (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {html_table_rows}
                </tbody>
            </table>

            <p class="highlight-note">
                * Services highlighted in red indicate cost increases greater than 10%
            </p>

            <div class="footer">
                <p>Generated on: {os.environ.get('REPORT_DATE', 'N/A')}</p>
                <p>This is an automated report from Azure Cost Management</p>
            </div>
        </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    if os.getenv('DEBUG', 'false').lower() == 'true':
        print("Email content:")
        print("From:", msg['From'])
        print("To:", msg['To'])
        print("Subject:", msg['Subject'])
        print("Body:")
        print(html_body)
        return  # Don't send email in debug mode

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

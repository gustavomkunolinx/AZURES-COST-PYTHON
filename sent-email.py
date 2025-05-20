
# Create the email message
msg = MIMEMultipart()
msg['From'] = email_sender
msg['To'] = ', '.join(email_recipients)
msg['Subject'] = 'Daily Azure Cost Update'

# Create the body of the email
template = Template('''
<html>
    <body>
        <h2 style="color:blue;"> Azure costs comparisiong yesterday vs -7d: </h2>
        <p> Total cost on {{ total_cost_date_1 }}: {{ total_cost_brls }} {{ cost_data[0]["currency"] }}</p>

        <h3 style="color:blue;"> Top 5 services by cost: </h3>
        <ol>
        {% for row in cost_data_sorted[:5] %}
            <li>{{ row["service"] }} - {{ row["cost"] }} {{ row["currency"] }}</li>
        {% endfor %}
        </ol>
    </body>
</html>
''')

body = template.render(
    total_cost_date_1=total_cost_date_1,
    cost_data=cost_data,
    cost_data_sorted=cost_data_sorted
)

msg.attach(MIMEText(body, 'html'))


if os.getenv('DEBUG', 'false').lower() == 'true':
    print("Email content:")
    print("From:", msg['From'])
    print("To:", msg['To'])
    print("Subject:", msg['Subject'])
    print("Body:")
    # Print the HTML body
    print(body)


# DISABLED SENT MAIL
# with smtplib.SMTP(email_smtp_server, email_smtp_port) as smtp:
#     smtp.ehlo()
#     smtp.starttls()
#     smtp.ehlo()
#     if not email_password:
#         raise ValueError("Email password is not set. Please check your environment variables.")
#     smtp.login("apikey", email_password)  # Use "apikey" as the login name and the API key as the password
#     smtp.send_message(msg)
#     print('Email sent successfully using SendGrid.')

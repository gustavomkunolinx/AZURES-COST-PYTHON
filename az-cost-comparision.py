import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import os
from datetime import datetime, timedelta
from jinja2 import Template
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve Azure credentials and other parameters from environment variables
subscription_id = os.getenv('subscription_id')
tenant_id = os.getenv('tenant_id')
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
email_sender = os.getenv('email_sender')
email_password = os.getenv('email_password')
email_smtp_server = os.getenv('email_smtp_server', 'smtp.office365.com')  # Default to Office365 SMTP
email_smtp_port = int(os.getenv('email_smtp_port', 587))  # Default to port 587
email_recipients = os.getenv('email_recipients', '').split(',')

# Debug print all parameters
print("Azure Subscription ID:", subscription_id)
print("Azure Tenant ID:", tenant_id)
print("Azure Client ID:", client_id)
print("Email Sender:", email_sender)
print("Email SMTP Server:", email_smtp_server)
print("Email SMTP Port:", email_smtp_port)
print("Email Recipients:", email_recipients)

# Authenticate with Azure AD and get access token
auth_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
auth_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'resource': 'https://management.azure.com/'
}
auth_response = requests.post(auth_url, data=auth_data)
access_token = auth_response.json()['access_token']


usage_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2019-11-01'
usage_data = {
    'type': 'Usage',
    'timeframe': 'Custom',
    'timePeriod': {
        'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT00:00:00Z'),
        'to': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT23:59:59Z')
    },
    'dataset': {
        'granularity': 'Daily',
        'aggregation': {
            'totalCost': {
                'name': 'Cost',
                'function': 'Sum'
            }
        },
        'grouping': [
            {
                'type': 'Dimension',
                'name': 'ServiceName'
            }
        ]
    }
}


usage_response = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data)

print("Usage Response:", json.dumps(usage_response.json(), indent=4))

# Extract the cost data and print the top 5 services by cost
cost_data = usage_response.json()['properties']['rows']


# Convert the list of lists to a list of dictionaries
cost_data = [
    {
        'cost': row[0],
        'date': row[1],
        'service': row[2],
        'currency': row[3]
    }
    for row in cost_data
]

# Calculate the total cost and the date of the total cost
total_cost = 0
total_cost_date = None
for row in cost_data:
    if total_cost_date is None or row['date'] > total_cost_date:
        total_cost_date = row['date']
        date_obj = datetime.strptime(str(total_cost_date), "%Y%m%d")
        total_cost_date_1 = date_obj.strftime("%Y-%m-%d")
    total_cost += row['cost']

# Sort the list of dictionaries by cost in descending order
cost_data_sorted = sorted(cost_data, key=lambda k: k['cost'], reverse=True)

# Print the total cost and its date
print(f'Total cost on {total_cost_date_1}: {total_cost} {cost_data[0]["currency"]}')

# Print the top 5 services by cost
print('Top 5 services by cost:')
for i, row in enumerate(cost_data_sorted[:6]):
    print(f"{i+1}. {row['service']} - {row['cost']} {row['currency']}")

list_items = [f"<li> {row['service']} - {row['cost']} {row['currency']}</li>" for row in cost_data_sorted]

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
        <p> Total cost on {{ total_cost_date_1 }}: {{ total_cost }} {{ cost_data[0]["currency"] }}</p>

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

with smtplib.SMTP(email_smtp_server, email_smtp_port) as smtp:
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    if not email_password:
        raise ValueError("Email password is not set. Please check your environment variables.")
    smtp.login("apikey", email_password)  # Use "apikey" as the login name and the API key as the password
    smtp.send_message(msg)
    print('Email sent successfully using SendGrid.')

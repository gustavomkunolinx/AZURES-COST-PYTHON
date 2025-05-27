import logging
import azure.functions as func
import requests
import json
import os
import locale
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils import azure_auth
from utils import azure_subscription_queries
from utils import email

# Load environment variables and set locale
load_dotenv()
locale.setlocale(locale.LC_ALL, '')



logging.info('Python timer trigger function executed.')

# Retrieve environment variables
subscription_id = os.getenv('subscription_id')
tenant_id = os.getenv('tenant_id')
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
email_sender = os.getenv('email_sender')
email_password = os.getenv('email_password')
email_smtp_server = os.getenv('email_smtp_server', 'smtp.office365.com')
email_smtp_port = int(os.getenv('email_smtp_port', 587))
email_recipients = os.getenv('email_recipients', '').split(',')
azure_api_version = str(os.getenv('azure_api_version', '2024-08-01'))

usage_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version={azure_api_version}'

# Authenticate
access_token = azure_auth.authenticate_with_azure(tenant_id, client_id, client_secret)

# Prepare payloads
usage_data_yesterday = azure_subscription_queries.get_usage_data(1)
usage_data_lastweek = azure_subscription_queries.get_usage_data(31)

# Make requests
usage_response_yesterday = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_yesterday)
usage_response_lastweek = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_lastweek)

# Process data
cost_data_yesterday = azure_subscription_queries.process_cost_data(usage_response_yesterday)
cost_data_lastweek = azure_subscription_queries.process_cost_data(usage_response_lastweek)

# Extract date from usage_data_yesterday
a_date_from = usage_data_yesterday['timePeriod']['from']
a_formatted_date = datetime.strptime(a_date_from, "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
print(f"Data extracted for comparison: {a_formatted_date}")

# Extract date from usage_data_yesterday
b_date_from = usage_data_lastweek['timePeriod']['from']
b_formatted_date = datetime.strptime(b_date_from, "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
print(f"Data extracted for comparison: {b_formatted_date}")

# Analytics and reporting
html_report = azure_subscription_queries.compare_service_costs(cost_data_yesterday, cost_data_lastweek, a_formatted_date, b_formatted_date)

print(html_report)

# Set report date environment variable for email
os.environ['REPORT_DATE'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Send email with proper parameters
email.send_email(
    html_table_rows=html_report,
    email_smtp_server=email_smtp_server,
    email_smtp_port=email_smtp_port,
    email_password=email_password,
    label_a=a_formatted_date,
    label_b=b_formatted_date
)

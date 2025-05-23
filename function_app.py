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

# Load environment variables and set locale
load_dotenv()
locale.setlocale(locale.LC_ALL, '')

# (Copy all your helper functions here: get_usage_data, extract_cost_data, process_cost_data, calculate_and_display_costs, compare_service_costs)

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)

def azure_cost_report_1(myTimer: func.TimerRequest) -> None:

    if myTimer.past_due:
        logging.info('The timer is past due!')

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
    usage_data_yesterday = get_usage_data(1)
    usage_data_lastweek = get_usage_data(31)

    # Make requests
    usage_response_yesterday = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_yesterday)
    usage_response_lastweek = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_lastweek)

    # Process data
    cost_data_yesterday = process_cost_data(usage_response_yesterday)
    cost_data_lastweek = process_cost_data(usage_response_lastweek)

    # Analytics and reporting
    html_report = compare_service_costs(cost_data_yesterday, cost_data_lastweek)

    # (Optional) Send email or log the report
    logging.info("Azure Cost Comparison Report:\n" + html_report)

import logging
import azure.functions as func
import requests
import json
import os
import locale
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils import azure
from utils import azure_subscription_queries
from utils import email

# Load environment variables and set locale
load_dotenv()
locale.setlocale(locale.LC_ALL, '')

app = func.FunctionApp()

def execute_cost_comparison(subscription_id):
    """
    Core function that executes the cost comparison logic.
    Can be called by both timer and HTTP triggers.
    """
    try:
        logging.info('Executing Azure cost comparison...')

        # Retrieve environment variables
        tenant_id = os.getenv('tenant_id')
        client_id = os.getenv('client_id')
        client_secret = os.getenv('client_secret')
        email_sender = os.getenv('email_sender')
        email_password = os.getenv('email_password')
        email_smtp_server = os.getenv('email_smtp_server', 'smtp.sendgrid.net')
        email_smtp_port = int(os.getenv('email_smtp_port', 587))
        email_recipients = os.getenv('email_recipients', '').split(',')
        azure_api_version = str(os.getenv('azure_api_version', '2024-08-01'))

        usage_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version={azure_api_version}'

        # Authenticate
        access_token = azure.authenticate_with_azure(tenant_id, client_id, client_secret)

        # Get subscription name
        subscription_name = azure.get_subscription_name(subscription_id, access_token)
        logging.info(f"Processing subscription: {subscription_name}")

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
        logging.info(f"Data extracted for comparison: {a_formatted_date}")

        # Extract date from usage_data_lastweek
        b_date_from = usage_data_lastweek['timePeriod']['from']
        b_formatted_date = datetime.strptime(b_date_from, "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
        logging.info(f"Data extracted for comparison: {b_formatted_date}")

        # Analytics and reporting
        html_report = azure_subscription_queries.compare_service_costs(cost_data_yesterday, cost_data_lastweek, a_formatted_date, b_formatted_date)

        # Set report date environment variable for email
        os.environ['REPORT_DATE'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Send email with proper parameters including subscription name
        email.send_email(
            html_table_rows=html_report,
            email_smtp_server=email_smtp_server,
            email_smtp_port=email_smtp_port,
            email_password=email_password,
            label_a=a_formatted_date,
            label_b=b_formatted_date,
            subscription_name=subscription_name
        )

        logging.info("Azure Cost Comparison Report generated and sent successfully")
        return {
            "status": "success",
            "message": "Cost comparison report generated and sent successfully",
            "report_date": os.environ.get('REPORT_DATE'),
            "subscription_name": subscription_name,
            "comparison_dates": {
                "current": a_formatted_date,
                "previous": b_formatted_date
            }
        }

    except Exception as e:
        logging.error(f"Error executing cost comparison: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to generate cost comparison report: {str(e)}"
        }

@app.timer_trigger(schedule="10 6 * * * *", arg_name="daily6am", run_on_startup=False, use_monitor=False)
def schedule_cost_report_1(daily6am: func.TimerRequest) -> None:
    """
    Timer-triggered function that runs the cost comparison on schedule.
    """
    if daily6am.past_due:
        logging.info('The timer is past due!')

    logging.info('Timer triggered Azure cost comparison function executed.')
    result_mvx_dev = execute_cost_comparison("bfb38ea5-2e52-42a4-86a8-b5ff06ef1178")
    result_mvx_prod = execute_cost_comparison("6e6145fd-2644-4673-96f0-a813a725ca4c")

    logging.info(f"Timer trigger result: DEV {result_mvx_dev} | PROD {result_mvx_prod}")

@app.route(route="cost-report", methods=["GET", "POST"])
def manual_cost_report_1(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function to manually start the cost comparison report.
    
    Usage:
    - GET /api/cost-report - Trigger the report generation
    - POST /api/cost-report - Trigger the report generation (supports JSON body for future parameters)
    
    Returns:
    - JSON response with status and details
    """
    logging.info('HTTP trigger function processed a request for manual cost report.')

    try:
        # Execute the cost comparison
        result_mvx_dev = execute_cost_comparison("bfb38ea5-2e52-42a4-86a8-b5ff06ef1178")
        
        if result_mvx_dev["status"] == "success":
            return func.HttpResponse(
                body=json.dumps(result_mvx_dev, indent=2),
                status_code=200,
                headers={"Content-Type": "application/json"}
            )
        else:
            return func.HttpResponse(
                body=json.dumps(result_mvx_dev, indent=2),
                status_code=500,
                headers={"Content-Type": "application/json"}
            )

    except Exception as e:
        error_response = {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }
        logging.error(f"HTTP trigger error: {str(e)}")
        return func.HttpResponse(
            body=json.dumps(error_response, indent=2),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

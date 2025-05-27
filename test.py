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
access_token = azure.authenticate_with_azure(tenant_id, client_id, client_secret)


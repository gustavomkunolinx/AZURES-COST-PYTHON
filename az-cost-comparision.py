import requests
import smtplib
import json
import os
import locale
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from jinja2 import Template
from dotenv import load_dotenv

######################## SYSTEM
# # Load environment variables from a .env file
load_dotenv()
locale.setlocale(locale.LC_ALL, '')

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

# Validate required environment variables
if not email_sender:
    raise ValueError("email_sender environment variable is not set.")
if not email_recipients or email_recipients == ['']:
    raise ValueError("email_recipients environment variable is not set.")

######################## END OF SYSTEM

######################## FUNCTIONS

def extract_cost_data(response):
    """
    Extract cost data from the Azure API response.

    Args:
        response (requests.Response): The response object from the Azure API.

    Returns:
        list: A list of cost data rows.

    Raises:
        KeyError: If the response JSON does not contain the expected structure.
    """
    if (
        isinstance(response.json(), dict)
        and 'properties' in response.json()
        and isinstance(response.json()['properties'], dict)
        and 'rows' in response.json()['properties']
    ):
        return response.json()['properties']['rows']
    else:
        print("Unexpected response structure:")
        print(json.dumps(response.json(), indent=2))
        raise KeyError("Response JSON does not contain 'properties' or 'rows' as expected.")

######################## END OF FUNCTIONS


if os.getenv('DEBUG', 'false').lower() == 'true':
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

usage_data_yesterday = {
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

usage_data_lastweek = {
    'type': 'Usage',
    'timeframe': 'Custom',
    'timePeriod': {
        'from': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%dT00:00:00Z'),
        'to': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%dT23:59:59Z')
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

######################## REQUESTS
usage_response_yesterday = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_yesterday)
usage_response_lastweek = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_lastweek)


if os.getenv('DEBUG', 'false').lower() == 'true':
    print("Usage Response:", json.dumps(usage_response_yesterday.json(), indent=4))
    print("Usage Response:", json.dumps(usage_response_lastweek.json(), indent=4))

######################## END OF REQUESTS


# Extract the cost data using the function
cost_data = extract_cost_data(usage_response_yesterday)
cost_data_lastweek = extract_cost_data(usage_response_lastweek)

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
total_cost_date_1 = "N/A"  # Initialize with a default value
for row in cost_data:
    if total_cost_date is None or row['date'] > total_cost_date:
        total_cost_date = row['date']
        date_obj = datetime.strptime(str(total_cost_date), "%Y%m%d")
        total_cost_date_1 = date_obj.strftime("%Y-%m-%d")
    total_cost += row['cost']

total_cost_brls = total_cost

# Sort the list of dictionaries by cost in descending order
cost_data_sorted = sorted(cost_data, key=lambda k: k['cost'], reverse=True)

# Print the total cost and its date
print(f'Total cost on {total_cost_date_1}: {total_cost_brls} {cost_data[0]["currency"]}')

# Print the top 5 services by cost
print('Top 5 services by cost:')
for i, row in enumerate(cost_data_sorted[:7]):
    print(f"{i+1}. ServiceName: {row['service']} - R${row['cost']} {row['currency']}")

# Review
list_items = [f"<li> ServiceName: {row['service']} - R${row['cost']} {row['currency']}</li>" for row in cost_data_sorted]
if os.getenv('DEBUG', 'false').lower() == 'true':
    print(f'check: {list_items}')


import requests
import os

azure_api_version = str(os.getenv('azure_api_version', '2024-08-01'))

def authenticate_with_azure(tenant_id, client_id, client_secret):
    """
    Authenticate with Azure AD and retrieve an access token.

    Returns:
        str: The access token for Azure API authentication.

    Raises:
        ValueError: If authentication fails or the response does not contain an access token.
    """
    auth_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/token'  # tenant_id is now passed as a parameter
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': 'https://management.azure.com/'
    }
    auth_response = requests.post(auth_url, data=auth_data)
    if auth_response.status_code != 200 or 'access_token' not in auth_response.json():
        raise ValueError("Failed to authenticate with Azure. Check your credentials.")
    return auth_response.json()['access_token']

def get_subscription_name(subscription_id, access_token):
    """
    Retrieve the Azure subscription display name from the Azure API.

    Args:
        subscription_id (str): The Azure subscription ID.
        access_token (str): The access token for Azure API authentication.

    Returns:
        str: The Azure subscription display name.

    Raises:
        ValueError: If the API call fails or the response doesn't contain a display name.
    """
    
    usage_url = f'https://management.azure.com/subscriptions/{subscription_id}/?api-version={azure_api_version}'
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(usage_url, headers=headers)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to retrieve subscription details. Status code: {response.status_code}")
    
    subscription_data = response.json()
    display_name = subscription_data.get('displayName')
    
    if not display_name:
        raise ValueError("Subscription display name not found in API response.")
    
    return display_name
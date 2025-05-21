
import requests

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


import requests
import json



# ------------------------------------------------------------ #
# Requests Handler 
# ------------------------------------------------------------ #

def send_post_request(url: str, data: dict):
    """
    Send a POST request to the specified URL with the given data.
    """

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error sending POST request to {url}: {e}")
        return None
    
def send_get_request(url: str, params: dict = None):
    """
    Send a GET request to the specified URL with the given parameters.
    """
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error sending GET request to {url}: {e}")
        return None



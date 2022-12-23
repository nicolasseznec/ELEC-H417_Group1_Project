import requests
from src.constants import REQUEST_METHODS


def construct_request(method, url, args=None):
    """
    Construct a request answering the expected pattern
    :param method: a method of the Request module ("get", "delete", "head", "post")
    :param url: The url of the request
    :return: The request if it answers the conditions of a request
    """
    request = {"method": method, "url": url, "args": args}
    if check_request_validity(request):
        return request
    return None


def check_request_validity(request):
    """
    Verifies that a given request has a valid format
    """
    mandatory_keys = ["method", "url", "args"]
    if type(request) is dict:
        for key in mandatory_keys:
            if key not in request:
                return False
        if request["method"] in REQUEST_METHODS:
            return True
    return False


def exec_request(request):
    """
    Executes a request
    :param request: The request
    :return: The result of the request
    """
    if check_request_validity(request):
        try:
            x = requests.request(request["method"], request["url"])
            if x.status_code == 200:
                return x.text
            else:
                return "Error " + str(x.status_code)
        except Exception as e:
            return e
    else:
        return "Invalid request syntax"




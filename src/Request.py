import requests
from constants import REQUEST_METHODS


def construct_request(method, url, args=None):
    request = {"method": method, "url": url, "args": args}
    if check_request_validity(request):
        return request
    return None


def check_request_validity(request):
    if type(request) is dict:
        if request["method"] in REQUEST_METHODS:
            return True
    return False


def exec_request(request):
    if check_request_validity(request):
        try:
            x = requests.request(request["method"], request["url"])
            if x.status_code == 200:
                return x.text
            else:
                return "Error " + str(x.status_code)
        except Exception as e:
            raise e
    else:
        return "Invalid request syntax"


# msg = construct_request("get", 'https://w3schools.com/python/demopage.htm')
# print(exec_request(msg))


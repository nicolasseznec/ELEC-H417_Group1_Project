import requests


def make_request(request):
    try:
        x = exec(request)
        print(x)
        print(x.text)
        if x.status_code == 200:
            return x.text
    except Exception as e:
        raise e

msg = "requests.get('https://w3schools.com/python/demopage.html')"
# msg = "str(requests.get('https://w3schools.com/python/demopage.htm'))"
yep = exec(msg)
print(make_request(msg))
import os, requests
from flask import Request


def token(request: Request):
    if not "Authorization" in request:
        return None, ("missing credentials", 401)

    token = request.headers["Authorization"]
    if not token:
        return None, ("missing credentials", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": token},
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
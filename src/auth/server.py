import jwt, datetime, os
from flask import Flask, request
from flask_mysqldb import MySQL
from dotenv import load_dotenv

load_dotenv()

server = Flask(__name__)
mysql = MySQL(server)

# MYSQL CONFIG
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = os.environ.get("MYSQL_PORT")


def createJWT(username, secret, authz):
    payload = {
        "username": username,
        "admin": authz,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
    }

    return jwt.encode(payload, secret, algorithm="HS256")


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return "missing credentials", 401

    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username,)
    )

    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return "invalid credentials", 401

        return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)

    return "invalid credentials", 401


@server.route("/validate", method=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "missing credentials", 401

    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded_jwt = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"]
        )
    except:
        return "Not authorized", 403

    return decoded_jwt, 200


if __name__ == "__main__":
    # Listen on localhost and other IP address
    server.run(host="0.0.0.0", port=5000, debug=True)

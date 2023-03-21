import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

server = Flask(__name__)

mongo_video = PyMongo(server, uri=os.environ.get("MONGO_URI_VIDEO"))
mongo_mp3 = PyMongo(server, uri=os.environ.get("MONGO_URI_MP3"))

fs_video = gridfs.GridFS(mongo_video.db)
fs_mp3 = gridfs.GridFS(mongo_mp3.db)

# Synchronous RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))


@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


@server.route("/upload", methods=["POST"])
def upload():
    try:
        access, err = validate.token(request)

        if err:
            return err, 401

        access = json.loads(access)

        if access["admin"]:
            if len(request.files) > 1 or len(request.files) < 1:
                return "exactly 1 file required", 400

            for _, f in request.files.items():
                channel = connection.channel()
                err = util.upload(f, fs_video, channel, access)

                channel.close()
                if err:
                    return err

            return "success!", 200
        else:
            return "not authorized", 401
    except Exception as err:
        print(err, flush=True)

        return "internal server error", 500


@server.route("/download", methods=["GET"])
def download():
    try:
        access, err = validate.token(request)

        if err:
            return err, 401

        access = json.loads(access)

        if access["admin"]:
            fid_string = request.args.get("fid")
            if not fid_string:
                return "missing fid", 400

            try:
                out = fs_mp3.get(ObjectId(fid_string))
                return send_file(out, download_name=f"{fid_string}.mp3"), 200
            except Exception as err:
                print(err)
                return "not found", 404

        return "not authorized", 401

    except Exception as err:
        print(err, flush=True)

        return "internal server error", 500


if __name__ == "__main__":
    server.run(host="0.0.0.0", port="8080")

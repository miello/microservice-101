import pika, json
from gridfs import GridFS

# RabbitMQ uses competing consumers pattern to distribute messages to workers
# which round robin the messages to the workers
from pika.spec import PERSISTENT_DELIVERY_MODE


def upload(f, fs: GridFS, channel, access):
    try:
        fid = fs.put(f)
    except Exception as err:
        print(err)
        return "internal server error", 500

    message = {"video_fid": str(fid), "mp3_fid": None, "username": access["username"]}

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            # Persistent message even if pod is crashed by making queue durable
            properties=pika.BasicProperties(delivery_mode=PERSISTENT_DELIVERY_MODE),
        )
    except Exception as err:
        print(err)

        fs.delete(file_id=fid)
        return "internal server error", 500

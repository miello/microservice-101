import pika, sys, os, time
from pymongo import MongoClient
import gridfs
from convert import to_mp3


def main():
    client = MongoClient(os.environ.get("MONGO_URI"))
    db_video = client.videos
    db_mp3s = client.mp3s

    # gridfs
    fs_videos = gridfs.GridFS(db_video)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # rabbitmq
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        try:
            err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
            if err:
                ch.basic_nack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as err:
            print(err)

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"), on_message_callback=callback, auto_ack=True
    )

    print("Waiting for messages. To exit press CTRL+C", flush=True)
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

import pika, json, tempfile, os
from bson.objectid import ObjectId
import moviepy.editor
from pika.spec import PERSISTENT_DELIVERY_MODE


def start(body, fs_videos, fs_mp3s, ch):
    message = json.loads(body)

    # empty temp file
    tf = tempfile.NamedTemporaryFile()

    # Video content
    out = fs_videos.get(ObjectId(message["video_fid"]))

    # add contents to temp file
    tf.write(out.read())

    # create audio
    audio = moviepy.editor.VideoFileClip(tf.name).audio
    tf.close()

    # save audio to a file
    tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(tf_path)

    # save audio to gridfs
    f = open(tf_path, "rb")
    data = f.read()
    fid = fs_mp3s.put(data)
    f.close()
    os.remove(tf_path)

    message["mp3_fid"] = str(fid)

    try:
        ch.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=PERSISTENT_DELIVERY_MODE),
        )
    except Exception as err:
        fs_mp3s.delete(fid)
        return "failed to publish message"

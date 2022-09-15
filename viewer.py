import cv2
import zmq
import base64
import json
import numpy as np
from flask import Flask, Response, request
from time import sleep
import threading
import warnings 
warnings.filterwarnings("ignore", category=DeprecationWarning)

app = Flask(__name__)

def runapp(timer):
    sleep(timer)                # Sleep prior to running app
    print("RUNNING TRACKER")    # Tell user it is running tracker
    import app                  # ALSO HAS TO RUN PARRALEL

try:
    with open('json/running.json', 'w') as file:
        file.write(json.dumps({"running": True}))
except:
    print("ERROR: Something occured when stopping stream")

t = threading.Thread(target=runapp, args=[1])
t.setDaemon(True)
t.start()
sleep(2)

def rec_vid(skt):
    while True:
        try:
            frame = skt.recv_string()
            img = base64.b64decode(frame)
            npimg = np.frombuffer(img, dtype=np.uint8)
            source = cv2.imdecode(npimg, 1)
            ret, jpeg = cv2.imencode('.jpg', source)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except KeyboardInterrupt:
            break

@app.route('/video_feed')
def video_feed():

    global socketthingy
    try:
        context = zmq.Context(1)
        footage_socket = context.socket(zmq.SUB)
        footage_socket.bind('tcp://*:5555')
        footage_socket.setsockopt_string(zmq.SUBSCRIBE, str(''))

        socketthingy = footage_socket
    except:
        footage_socket = socketthingy
        print(str(footage_socket))
        footage_socket.disconnect('tcp://*:5555')
        context = zmq.Context(1)
        footage_socket = context.socket(zmq.SUB)
        footage_socket.bind('tcp://*:5555')
        footage_socket.setsockopt_string(zmq.SUBSCRIBE, str(''))
    print(str(footage_socket))
    # global video
    temp = Response(rec_vid(footage_socket),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    return temp

if __name__ == '__main__':
    # Use this to run VITM when called https://stackoverflow.com/questions/27474663/run-function-in-background-and-continue-with-program
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)

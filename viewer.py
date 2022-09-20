import cv2
import zmq
import base64
import json
import numpy as np
from flask import Flask, Response, request
from time import sleep
import threading

app = Flask(__name__)

# Starts traffic tracking so that it can be run with threading
def runapp(timer):
    sleep(timer)                # Sleep prior to running app
    print("RUNNING TRACKER")    # Tell user it is running tracker
    import app                  # ALSO HAS TO RUN PARRALEL

try:
    with open('json/running.json', 'w') as file: file.write(json.dumps({"running":True}))
except:
    print("ERROR: Something occured when stopping stream")

t = threading.Thread(target=runapp, args=[1])
t.setDaemon(True)
t.start()
sleep(2)
TCP_IP = 'localhost'
TCP_PORT = 5550
context = zmq.Context()


def rec_vid(skt):
    while True:
        try:
            frame = skt.recv_string()
            img = base64.b64decode(frame)
            npimg = np.fromstring(img, dtype=np.uint8)
            source = cv2.imdecode(npimg, 1)
            # cv2.imshow("Stream", source)
            # cv2.waitKey(1)
            # if(cv2.waitKey(1)&0xFF==ord('q')):break
            ret, jpeg = cv2.imencode('.jpg', source)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except KeyboardInterrupt:
            break




@app.route('/video_feed')
def video_feed():
    try:
        context = zmq.Context(1)
        footage_socket = context.socket(zmq.SUB)
        footage_socket.bind('tcp://*:5555')
        footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))


    except:
        pass

    print(str(footage_socket))
    # global video
    temp = Response(rec_vid(footage_socket),mimetype='multipart/x-mixed-replace; boundary=frame')
    # footage_socket.disconnect('tcp://*:5555')
    
    return temp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False) # Use this to run VITM when called https://stackoverflow.com/questions/27474663/run-function-in-background-and-continue-with-program


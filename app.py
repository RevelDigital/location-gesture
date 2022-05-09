import cv2
import time
import mouse
import numpy as np
import mediapipe as mp
from math import atan2, pi, trunc
import serial
import json
import requests
from threading import Timer
import queue
import os 

global canSend
canSend = True
def startLimit():
    global canSend;
    canSend = True;
    Timer(.1, startLimit).start()
startLimit();

#Function that calculates distance between two points
def distance(x1, y1, x2, y2):
    """
    calculates distance between two points
    x1, y1: x and y coordinates of point 1
    x2, y2: x and y coordinates of point 2
    """
    #Calculate distance between two points
    return ((x2 - x1)**2 + (y2 - y1)**2)**0.5

def json_to_dict(filename):
    with open(filename) as f:
        out = json.load(f)
    f.close()
    return out

try:
    setup_file = json_to_dict(r'/home/pi/Desktop/location-gesture-main/SETUP.json')
    #Opens serial port on default 9600,8,N,1 no timeout
    ser = serial.Serial("/dev/ttyS0")
    #Prints the port that is really being used
    print("Serial port being used: " + str(ser.name))
    if(setup_file["serialOutput"] == "True"):
        print("Serial Output: ON")
    else:
        print("Serial Output: OFF")
    if(setup_file["outputInTerminal"] == "True"):
        print("WILL Output in Terminal")
    else:
        print("WILL NOT Output in Terminal")

    #Initialize mediapipe
    mpHands     = mp.solutions.hands            # hands = mpHands(x1, y1, x2, y2)
    hands       = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7) #more hands
    mpDraw      = mp.solutions.drawing_utils    # draw on the image

    #Load class names
    f           = open('/home/pi/Desktop/location-gesture-main/gesture.names', 'r')    #
    classNames  = f.read().split('\n')          #
    f.close()                                   #   

    #Which webcam to use 0 = main, 1 = secondary etc
    which_webcam = 0
    #Initialize the webcam
    cap         = cv2.VideoCapture(which_webcam, cv2.WND_PROP_FULLSCREEN)
    #Average x and y coordinates of the hands
    avx_list, avy_list, size_list  = [], [], []    #average x and y points

    #Average x and y of hand
    avx, avy, size        = 0, 0, 0                #             

    #Is a hand detected?
    activate_gesture    = False

    while True:
        #Read each frame from the webcam
        _, frame        = cap.read()                #
        x, y, c         = frame.shape               # 
         
        width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height  = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        #Half of frame width
        half_width  = int(width/2)

        #First quarter of frame width
        first_quarter_width  = int(width/4)

        #Last quarter of frame width
        last_quarter_width  = int(width - first_quarter_width)

        #First eighth of frame width
        first_eighth_width  = int(width/8)

        #Last eighth of frame width
        last_eighth_width  = int(width - first_eighth_width)

        if(setup_file["quadrantVisualization"] == "True"):
            cv2.line(img=frame, pt1=(first_quarter_width, 40), pt2=(first_quarter_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(last_quarter_width, 40), pt2=(last_quarter_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(first_eighth_width, 40), pt2=(first_eighth_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(last_eighth_width, 40), pt2=(last_eighth_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(half_width, 20), pt2=(half_width, int(height-20)), color=(0, 0, 255), thickness=2, lineType=8, shift=0)

        #Actual frame size
        width = 480

        #Half of frame width
        half_width  = int(width/2)                  #

        #First quarter of frame width
        first_quarter_width  = int(width/4)         #

        #Last quarter of frame width
        last_quarter_width  = int(width - first_quarter_width)

        #First eighth of frame width
        first_eighth_width  = int(width/8)          #

        #Last eighth of frame width
        last_eighth_width  = int(width - first_eighth_width)
        
        #Flip the frame vertically
        frame           = cv2.flip(frame, 1)        #
        framergb        = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        #Get hand landmark prediction
        result          = hands.process(framergb)   #

        #The predicted gesture
        className       = ''                        #
        
        #Average x and y of palm
        avg_palm_x, avg_palm_y      = 0, 0          #
        
        #palm           : x, y
        palm            = [0,0]                     #x,y
        #thumb         : tip = 4,  base = 1
        thumbRaised     = True                      #is the thumb raised?
        thumbFingers_x, thumbFingers_y  = [0, 0], [0, 0]    #tip, base
        #index         : tip = 8,  base = 5
        indexRaised     = True                      #is the index finger raised?
        indexFingers_x, indexFingers_y  = [0, 0], [0, 0]    #tip, base
        #middle        : tip = 12, base = 9
        middleRaised    = True                      #is the middle finger raised?
        middleFingers_x, middleFingers_y = [0, 0], [0, 0]   #tip, base
        #ring          : tip = 16, base = 13
        ringRaised      = True                      #is the ring finger raised?
        ringFingers_x, ringFingers_y   = [0, 0], [0, 0]     #tip, base
        #pinky         : tip = 20, base = 17
        pinkyRaised     = True                      #is the pinky finger raised?
        pinkyFingers_x, pinkyFingers_y  = [0, 0], [0, 0]    #tip, base
        
        #Post process the result
        if  result.multi_hand_landmarks:
            landmarks   = []     #Landmarks of each hand
            #Draw lines between last five average x and y cooordinates except the first and last
            
            for handslms in result.multi_hand_landmarks:
                avx, avy= 0, 0      #average x, y of all the hand
                index   = 0         #index of the hand

                for lm in handslms.landmark:

                    lmx = round(int(lm.x * x), 3) #x coord of landmark
                    lmy = round(int(lm.y * y), 3) #y coord of landmark
                    avx += lmx
                    avy += lmy
                    
                    #label each point with a number
                    cv2.putText(frame, str(index), (int(lmx*1.3), int(lmy*0.8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (12*index, 0, 255-12*index), 1)
                    landmarks.append([lmx, lmy])  #add the point to the landmarks list

                    # palm   :  x, y
                    # thumb  :  tip = 4,  base = 1
                    # index  :  tip = 8,  base = 5
                    # middle :  tip = 12, base = 9
                    # ring   :  tip = 16, base = 13
                    # pinky  :  tip = 20, base = 17
                    
                    # palm
                    if  index               == 0:
                        palm                = [lmx, lmy] #x,y

                    # thumb
                    elif index              == 1:
                        thumbFingers_x[1]   = lmx #base x
                        thumbFingers_y[1]   = lmy #base y
                    elif index              == 4:
                        thumbFingers_x[0]   = lmx #tip x
                        thumbFingers_y[0]   = lmy #tip y
                    
                    # index
                    elif index              == 5:
                        indexFingers_x[1]   = lmx #base x
                        indexFingers_y[1]   = lmy #base y
                    elif index              == 8:
                        indexFingers_x[0]   = lmx #tip x
                        indexFingers_y[0]   = lmy #tip y
                    
                    # middle
                    elif index              == 9:
                        middleFingers_x[1]  = lmx #base x
                        middleFingers_y[1]  = lmy #base y
                    elif index              == 12:
                        middleFingers_x[0]  = lmx #tip x
                        middleFingers_y[0]  = lmy #tip y
                    
                    # ring
                    elif index              == 13:
                        ringFingers_x[1]    = lmx #base x
                        ringFingers_y[1]    = lmy #base y
                    elif index              == 16:
                        ringFingers_x[0]    = lmx #tip x
                        ringFingers_y[0]    = lmy #tip y
                    
                    # pinky
                    elif index              == 17:
                        pinkyFingers_x[1]   = lmx #base x
                        pinkyFingers_y[1]   = lmy #base y
                    elif index              == 20:
                        pinkyFingers_x[0]   = lmx #tip x
                        pinkyFingers_y[0]   = lmy #tip y
                    
                    index += 1
                
                #Get range of x and y, for use in calculating the hand's size
                x_range = max(landmarks, key=lambda x: x[0])[0] - min(landmarks, key=lambda x: x[0])[0]
                y_range = max(landmarks, key=lambda x: x[1])[1] - min(landmarks, key=lambda x: x[1])[1]

                #Size of hand relative to screen
                size = round((x_range+y_range)/(width+height), 2)

                #Average of all the hand
                avx, avy                    = round(avx / len(handslms.landmark), 1), round(avy / len(handslms.landmark), 1)
                #Average of the hand in relation to the palm
                avg_palm_x, avg_palm_y      = round((palm[0] + avx)/2, 1), round((palm[1] + avy)/2, 1)
                #Distance of the thumb in relation to the palm
                dist_hand                   = distance(avg_palm_x, avg_palm_y, avx, avy)
                
                #Store last fifteen average x and y cooordinates
                if  avx != 0 and avy != 0:
                    avx_list.append(avx)
                    avy_list.append(avy)
                    size_list.append(size)
                if  len(avx_list) > 15:
                    avx_list.pop(0)
                    avy_list.pop(0)
                    size_list.pop(0)

                #Setting a sensitivity for how much each finger is considered raised or not
                sensitivity = 0.6
                
                #Index finger exists in the correct range to determine if the hand is in frame
                if  indexFingers_x[0]       != 0 :
                    thumbRaised             = (dist_hand < distance(thumbFingers_x[0],  thumbFingers_y[0],  avg_palm_x, avg_palm_y)*sensitivity)
                    indexRaised             = (dist_hand < distance(indexFingers_x[0],  indexFingers_y[0],  avg_palm_x, avg_palm_y)*sensitivity)
                    middleRaised            = (dist_hand < distance(middleFingers_x[0], middleFingers_y[0], avg_palm_x, avg_palm_y)*sensitivity)
                    ringRaised              = (dist_hand < distance(ringFingers_x[0],   ringFingers_y[0],   avg_palm_x, avg_palm_y)*sensitivity)
                    pinkyRaised             = (dist_hand < distance(pinkyFingers_x[0],  pinkyFingers_y[0],  avg_palm_x, avg_palm_y)*sensitivity)
                    
                #Print if fingers are raised or not
                cv2.putText(frame, 'Thumb Raised: ' + str(thumbRaised),  (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if thumbRaised == True:
                    thumbR = 1
                else:
                    thumbR = 0
                cv2.putText(frame, 'Index Raised: ' + str(indexRaised),  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if indexRaised == True:
                    indexR = 1
                else:
                    indexR = 0
                cv2.putText(frame, 'Middle Raised: '+ str(middleRaised), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if middleRaised == True:
                    middleR = 1
                else:
                    middleR = 0
                cv2.putText(frame, 'Ring Raised: '  + str(ringRaised),   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if ringRaised == True:
                    ringR = 1
                else:
                    ringR = 0
                cv2.putText(frame, 'Pinky Raised: ' + str(pinkyRaised),  (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if pinkyRaised == True:
                    pinkyR = 1
                else:
                    pinkyR = 0

                if indexRaised == False and middleRaised == False and ringRaised == False and pinkyRaised == False:
                    isFist = True
                else:
                    isFist = False
                
                if(setup_file["crashChrisComputer"] == "True"):
                    #reset index
                    index = 0
                    #Drawing landmarks on frames
                    mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)

                #Reset index
                index = 0

                #Drawing landmarks on frames
                mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)
        
        # if the hand is in the frame
        if  len(avx_list) > 1:

            if(setup_file["mouseControl"] == "True"):
                #move mouse to the center of the palm
                mouse.move(int((avg_palm_x-200)*8-400), int((avg_palm_y-200)*4-400))
            
            #Is the hand in a held position?
            isHeld = (not indexRaised) and (not middleRaised) and (not ringRaised) and (not pinkyRaised)

            #Check which quadrant the avg palm is in
            if(avg_palm_x>0 and avg_palm_x<first_eighth_width):
                quadrent = 1
            elif(avg_palm_x>first_eighth_width  and avg_palm_x<first_quarter_width):
                quadrent = 2
            elif(avg_palm_x>first_quarter_width and avg_palm_x<last_quarter_width):
                quadrent = 3
            elif(avg_palm_x>last_quarter_width  and avg_palm_x<last_eighth_width):
                quadrent = 4
            elif(avg_palm_x>last_eighth_width):
                quadrent = 5
            else:
                quadrent = 0

            #Display which quadrant the hand is in
            cv2.putText(frame, str(str(quadrent) + ", " + str(avx) + ", " + str(avy) + ", " + str(isFist)),  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
            if(setup_file["serialOutput"] == "True" and canSend):
                if  indexFingers_x[0]       != 0 :
                    ser.write(bytes('gesture' + '|' + str(quadrent) + '|' + str(round(avx)) + '|' + str(round(avy)) + '|' + str(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))) + '|' + str(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))+ '|' + str(indexR) + '|' + str(middleR) + '|' + str(ringR) + '|' + str(pinkyR) + '|' + str(isFist) + '\n', encoding='utf8'))
                canSend = False
            #Display hand size
            cv2.putText(frame, 'size: ' + str(size),  (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1)
            
            if(setup_file["outputInTerminal"] == "True"):
                if  indexFingers_x[0]       != 0 :
                    print(str(str(quadrent) + ', ' + str(round(avx)) + ', ' + str(round(avy)) + ', ' + str(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))) + ', ' + str(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))) + ', ' + str(indexR) + ', ' + str(middleR) + ', ' + str(ringR) + ', ' + str(pinkyR) + ', ' + str(isFist)))
                #(quadrant, x-coord of hand, y-coord of hand, camera res width, camera res height, index finger raised, middle finger raised, ring finger raised, pinky finger raised, is fist?)

            #if the hand is not held
            if(setup_file["mouseControl"] == "True"):
                if  not isHeld:
                    if  mouse.is_pressed('left'):
                        mouse.release('left')
                        print("released")
                    elif not indexRaised:
                        mouse.click('left')
                        print("clicked")
                        time.sleep(0.25)
                    elif not pinkyRaised:
                        mouse.click('right')
                        print("right clicked")
                        time.sleep(0.3)
            
                #If the hand is held
                if  isHeld:
                    if  not mouse.is_pressed('left'):
                        mouse.press('left')
                        print("pressed")
            
        #Show the final output
        cv2.namedWindow("Output", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        if(setup_file["videoFeedPortrait"] == "True"):
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        cv2.imshow("Output", frame)

        #Press q to quit
        if  cv2.waitKey(1) == ord('q'):
            ser.close()
            break

    #Release the webcam and destroy all active windows
    cap.release()

    #Destroy all windows
    cv2.destroyAllWindows()
except serial.SerialException as e:
    print(str(e))
    os.system('sudo reboot now')
    
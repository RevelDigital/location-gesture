# import the necessary packages
import cv2
import time
import mouse
import numpy as np
import mediapipe as mp
from math import atan2, pi, trunc
import serial
import json
import requests

def json_to_dict(filename):
    with open(filename) as f:
        out = json.load(f)
    f.close()
    return out

setup_file = json_to_dict(r'SETUP.json')

#opens serial port on default 9600,8,N,1 no timeout
ser = serial.Serial(setup_file["portLocation"])
print("Serial port being used: ")
print(ser.name) #prints the port that is really being used
print("Thumb up for PLAY")
print("Index up for PAUSE")


# initialize mediapipe
mpHands     = mp.solutions.hands            # hands = mpHands(x1, y1, x2, y2)
hands       = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7) #more handssssssssssss
mpDraw      = mp.solutions.drawing_utils    # draw on the image

# Load class names
f           = open('gesture.names', 'r')    #
classNames  = f.read().split('\n')          #
f.close()                                   #   

# Initialize the webcam
cap         = cv2.VideoCapture(0)           #

# average x and y coordinates of the hands
avx_list, avy_list  = [], []    #average x and y points

# is a hand detected
activate_gesture    = False #determines whether the gesture is activated

# a function that calculates distance between two points
def distance(x1, y1, x2, y2):
    """
    calculates distance between two points
    x1, y1: x and y coordinates of point 1
    x2, y2: x and y coordinates of point 2
    """
    return ((x2 - x1)**2 + (y2 - y1)**2)**0.5   #calculate distance between two points

# while true
while True:
    # Read each frame from the webcam
    _, frame        = cap.read()                #
    x, y, c         = frame.shape               #  
    #dimensions = cap.shape
    #width = cap.shape[1]
    width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height  = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    cv2.line(img=frame, pt1=(40, 40), pt2=(40, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
    cv2.line(img=frame, pt1=(200, 40), pt2=(200, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
    cv2.line(img=frame, pt1=(int(width-200), 40), pt2=(int(width-200), int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
    cv2.line(img=frame, pt1=(int(width-40), 40), pt2=(int(width-40), int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 

    
    # Flip the frame vertically
    frame           = cv2.flip(frame, 1)        #
    framergb        = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Get hand landmark prediction
    result          = hands.process(framergb)   #

    # The predicted gesture
    className       = ''                        #

    # average x and y of hand
    avx, avy        = 0, 0                 #             

    # average x and y of palm
    avg_palm_x, avg_palm_y      = 0, 0          #
    
    #palm           : x, y
    palm            = [0,0]                     #x,y
    # thumb         : tip = 4,  base = 1
    thumbRaised     = True                      #is the thumb raised?
    thumbFingers_x, thumbFingers_y  = [0, 0], [0, 0]    #tip, base
    # index         : tip = 8,  base = 5
    indexRaised     = True                      #is the index finger raised?
    indexFingers_x, indexFingers_y  = [0, 0], [0, 0]    #tip, base
    # middle        : tip = 12, base = 9
    middleRaised    = True                      #is the middle finger raised?
    middleFingers_x, middleFingers_y = [0, 0], [0, 0]   #tip, base
    # ring          : tip = 16, base = 13
    ringRaised      = True                      #is the ring finger raised?
    ringFingers_x, ringFingers_y   = [0, 0], [0, 0]     #tip, base
    # pinky         : tip = 20, base = 17
    pinkyRaised     = True                      #is the pinky finger raised?
    pinkyFingers_x, pinkyFingers_y  = [0, 0], [0, 0]    #tip, base
    
    # post process the result
    if  result.multi_hand_landmarks:
        landmarks   = []     #landmarks of each hand
        for handslms in result.multi_hand_landmarks:

            avx, avy= 0, 0      #average x, y of all the hand
            index   = 0         #index of the hand

            for lm in handslms.landmark:

                lmx = round(int(lm.x * x), 3) #x of landmark
                lmy = round(int(lm.y * y), 3) #y of landmark
                avx += lmx #add x of landmark to the average x
                avy += lmy #add y of landmark to the average y
                
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
            
            # average of all the hand
            avx, avy                    = round(avx / len(handslms.landmark), 1), round(avy / len(handslms.landmark), 1)
            #average of the hand in relation to the palm
            avg_palm_x, avg_palm_y      = round((palm[0] + avx)/2, 1), round((palm[1] + avy)/2, 1)
            #distance of the thumb in relation to the palm
            dist_hand                   = distance(avg_palm_x, avg_palm_y, avx, avy)
            
            #index finger exists in the correct range to determine if the hand is in frame
            if  indexFingers_x[0]       != 0 :
                thumbRaised             = (dist_hand < distance(thumbFingers_x[0],  thumbFingers_y[0],  avg_palm_x, avg_palm_y))
                indexRaised             = (dist_hand < distance(indexFingers_x[0],  indexFingers_y[0],  avg_palm_x, avg_palm_y))
                middleRaised            = (dist_hand < distance(middleFingers_x[0], middleFingers_y[0], avg_palm_x, avg_palm_y))
                ringRaised              = (dist_hand < distance(ringFingers_x[0],   ringFingers_y[0],   avg_palm_x, avg_palm_y))
                pinkyRaised             = (dist_hand < distance(pinkyFingers_x[0],  pinkyFingers_y[0],  avg_palm_x, avg_palm_y))
                
            #print if fingers are raised or not
            #cv2.putText(frame, 'Thumb Raised: ' + str(thumbRaised),  (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            #cv2.putText(frame, 'Index Raised: ' + str(indexRaised),  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            #cv2.putText(frame, 'Middle Raised: '+ str(middleRaised), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            #cv2.putText(frame, 'Ring Raised: '  + str(ringRaised),   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            #cv2.putText(frame, 'Pinky Raised: ' + str(pinkyRaised),  (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            
            if(setup_file["crashChrisComputer"] == "True"):
                #reset index
                index = 0
                # Drawing landmarks on frames
                mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)

            # Drawing landmarks on frames
            mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)

    # store last five average x and y cooordinates
    if  avx != 0 and avy != 0:
        avx_list.append(avx)
        avy_list.append(avy)
    if  len(avx_list) > 5:
        avx_list.pop(0)
        avy_list.pop(0)
    
    # draw lines based on the average x and y
    #for i in range(len(avx_list)):
        #cv2.line(frame, (int(avx_list[i]*1.3), int(avy_list[i]*0.8)), (int(avx_list[i-1]*1.3), int(avy_list[i-1]*0.8)), (0, 0, 255), 1)
    
    # if the hand is in the frame
    if  len(avx_list) > 1:

        if(setup_file["mouseControl"] == "True"):
            #move mouse to the center of the palm
            mouse.move(int((avg_palm_x-200)*8-400), int((avg_palm_y-200)*4-400))
        
        #is the hand in a held position?
        isHeld = (not indexRaised) and (not middleRaised) and (not ringRaised) and (not pinkyRaised)

        if (avg_palm_x > 200 and avg_palm_x < int(width-200)):
            cv2.putText(frame, '0',  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)
        elif (avg_palm_x > 40 and avg_palm_x < 200):
            cv2.putText(frame, '-1',  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)
        elif (avg_palm_x < 40):
            cv2.putText(frame, '-2',  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)
        elif (avg_palm_x > int(width-200) and avg_palm_x < int(width-40)):
            cv2.putText(frame, '1',  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)
        elif (avg_palm_x > int(width-40)):
            cv2.putText(frame, '2',  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)
        elif (len(avx_list) > 1):
            cv2.putText(frame, 'Hand not Found',  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)
        #elif (avg_palm_x > 200 and avg_palm_x < int(width-200) and str(thumbRaised)==True):
            #cv2.putText(frame, 'PLAY' + str(thumbRaised),  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)
        #elif (avg_palm_x > 200 and avg_palm_x < int(width-200) and str(indexRaised)==True):
            #cv2.putText(frame, 'PAUSE' + str(indexRaised),  (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1)

            
        

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
        
            #if the hand is held
            if  isHeld:
                if  not mouse.is_pressed('left'):
                    mouse.press('left')
                    print("pressed")
        
    # Show the final output
    cv2.imshow("Output", frame)

    # Press q to quit
    if  cv2.waitKey(1) == ord('q'):
        ser.close()
        break

# release the webcam and destroy all active windows
cap.release()

# destroy all windows
cv2.destroyAllWindows()
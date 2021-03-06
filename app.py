# import the necessary packages
import cv2
import time
import mouse
import mediapipe as mp
import serial
import json
from threading import Timer
import os 
import numpy as np

global canSend
canSend = True
def startLimit():
    global canSend;
    canSend = True;
    Timer(.1, startLimit).start()
startLimit();

# for keeping landmarks just in case
last_landmarks = False
countdown = 0

# a function that calculates distance between two points
def distance(x1, y1, x2, y2):
    """
    calculates distance between two points
    x1, y1: x and y coordinates of point 1
    x2, y2: x and y coordinates of point 2
    """
    return ((x2 - x1)**2 + (y2 - y1)**2)**0.5   #calculate distance between two points

def json_to_dict(filename):
    try:
        with open(filename) as f:out = json.load(f)
        f.close()
        return out
    except:
        print("Error: file not found")
        quit()
try:
    setup_file = json_to_dict('SETUP.json')

    #ser.open()
    if(setup_file["serialOutput"] == "True"):
        print("Serial Output: ON")
        #opens serial port on default 9600,8,N,1 no timeout # Tutorial https://stackoverflow.com/questions/16701401/python-and-serial-how-to-send-a-message-and-receive-an-answer
        ser = serial.Serial("/dev/ttyUSB0")
        print("Serial port being used: " + str(ser.name)) #prints the port that is really being used
    else:print("Serial Output: OFF")
    if(setup_file["outputInTerminal"] == "True"):print("WILL Output in Terminal")
    else:print("WILL NOT Output in Terminal")
    print("Thumb up for ACTION")

    # initialize mediapipe
    mpHands     = mp.solutions.hands            # hands = mpHands(x1, y1, x2, y2)
    hands       = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7) #more hands
    mpDraw      = mp.solutions.drawing_utils    # draw on the image
    f           = open('gesture.names', 'r')    # Load class names
    classNames  = f.read().split('\n')          #
    f.close()                                   #   
    which_webcam = 0#which webcam to use 0 = main, 1 = secondary etc
    cap         = cv2.VideoCapture(which_webcam)# Initialize the webcam
    avx_list,avy_list,size_list=[],[],[] # average x and y coordinates of the hands. average x and y points
    avx,avy,size=0,0,0 # average x and y of hand
    activate_gesture    = False #determines whether the gesture is activated

    # cropped location
    crop_x=setup_file["camera_zone"]["x"]
    crop_y=setup_file["camera_zone"]["y"]
    crop_w=setup_file["camera_zone"]["w"]
    crop_h=setup_file["camera_zone"]["h"]

    # while true
    while True:
        _,frame=cap.read()# Read each frame from the webcam
        frame=frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]# Resize the frame to a smaller size based on x, y, width, height
        x,y,c=frame.shape  
        #dimensions = cap.shape
        #width = cap.shape[1]
        width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        awid = width
        height  = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        ahit = height
        

        half_width  = int(width/2)# half of frame width
        first_quarter_width  = int(width/4)# first quarter of frame width
        last_quarter_width  = int(width - first_quarter_width)# last quarter of frame width
        first_eighth_width  = int(width/8)# first eighth of frame width
        last_eighth_width  = int(width - first_eighth_width)# last eighth of frame width
        
        if(setup_file["quadrantVisualization"] == "True"):
            cv2.line(img=frame, pt1=(first_quarter_width, 40), pt2=(first_quarter_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(last_quarter_width, 40), pt2=(last_quarter_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(first_eighth_width, 40), pt2=(first_eighth_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(last_eighth_width, 40), pt2=(last_eighth_width, int(height-40)), color=(255, 0, 0), thickness=3, lineType=8, shift=0) 
            cv2.line(img=frame, pt1=(half_width, 20), pt2=(half_width, int(height-20)), color=(0, 0, 255), thickness=2, lineType=8, shift=0)

        # actual frame size IDK why id does this but this is the number that maintains accuracy for the hand detection
        width = 480
        half_width  = int(width/2)# half of frame width
        first_quarter_width  = int(width/4)# first quarter of frame width
        last_quarter_width  = int(width - first_quarter_width)# last quarter of frame width
        first_eighth_width  = int(width/8)# first eighth of frame width
        last_eighth_width  = int(width - first_eighth_width)# last eighth of frame width
        frame           = cv2.flip(frame, 1)# Flip the frame vertically
        framergb        = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result          = hands.process(framergb)# Get hand landmark prediction
        className       = ''# The predicted gesture

        frame =  np.zeros((int(ahit),int(awid),3),dtype=np.uint8) #test_fr=np.zeros(shape=[ht,wt,ch],dtype=np.uint8)
        frame[:]=(25,0,0)
        # # average x and y of hand
        # avx, avy        = 0, 0                      #             
        # size = 0;
        
        # average x and y of palm
        avg_palm_x, avg_palm_y      = 0, 0          #
        
        palm=[0,0]#palm           : x, y
        
        # thumb         : tip = 4,  base = 1
        thumb_R=True                      #is the thumb _R?
        thumb_x,thumb_y=[0,0],[0,0]    #tip, base
        # index         : tip = 8,  base = 5
        index_R=True                      #is the index finger _R?
        index_x,index_y=[0,0],[0,0]    #tip, base
        # middle        : tip = 12, base = 9
        middle_R=True                      #is the middle finger _R?
        middle_x,middle_y=[0,0],[0,0]   #tip, base
        # ring          : tip = 16, base = 13
        ring_R=True                      #is the ring finger _R?
        ring_x,ring_y=[0,0],[0,0]     #tip, base
        # pinky         : tip = 20, base = 17
        pinky_R=True                      #is the pinky finger _R?
        pinky_x,pinky_y=[0,0],[0,0]    #tip, base
        
        # post process the result
        if  last_landmarks and countdown < 15:
            if not result.multi_hand_landmarks:
                result.multi_hand_landmarks = last_landmarks
                countdown +=1
            landmarks=[]    #landmarks of each hand
            # draw lines between last five average x and y cooordinates except the first and last
            
            for handslms in result.multi_hand_landmarks:
                avx,avy=0,0         #average x, y of all the hand
                index=0             #index of the hand

                for lm in handslms.landmark:

                    lmx=round(int(lm.x*x),3) #x of landmark
                    lmy=round(int(lm.y*y),3) #y of landmark
                    avx+=lmx #add x of landmark to the average x
                    avy+=lmy #add y of landmark to the average y
                    
                    #label each point with a number
                    # cv2.putText(frame, str(index), (int(lmx*1.3), int(lmy*0.8)), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (255, 255, 255), 1)
                    cv2.circle(frame, (int(lmx*1.3), int(lmy*0.8)), 2, (19,239,239), 1)
                    landmarks.append([lmx, lmy])  #add the point to the landmarks list

                    # palm   :  x, y
                    # thumb  :  tip = 4,  base = 1
                    # index  :  tip = 8,  base = 5
                    # middle :  tip = 12, base = 9
                    # ring   :  tip = 16, base = 13
                    # pinky  :  tip = 20, base = 17
                    if index==0:palm=[lmx,lmy]                      # palm
                    elif index==1:thumb_x[1],thumb_y[1]=lmx,lmy     # thumb tip
                    elif index==4:thumb_x[0],thumb_y[0]=lmx,lmy     # thumb base
                    elif index==5:index_x[1],index_y[1]=lmx,lmy     # index tip
                    elif index==8:index_x[0],index_y[0]=lmx,lmy     # index base
                    elif index==9:middle_x[1],middle_y[1]=lmx,lmy   # middle tip
                    elif index==12:middle_x[0],middle_y[0]=lmx,lmy  # middle base
                    elif index==13:ring_x[1],ring_y[1]=lmx,lmy      # ring tip
                    elif index==16:ring_x[0],ring_y[0]=lmx,lmy      # ring base
                    elif index==17:pinky_x[1],pinky_y[1]=lmx,lmy    # pinky tip
                    elif index==20:pinky_x[0],pinky_y[0]=lmx,lmy    # pinky base
                    index += 1
                x_range=max(landmarks,key=lambda x:x[0])[0]-min(landmarks,key=lambda x:x[0])[0] # get range of x and y, for use in calculating the hand's size
                y_range=max(landmarks,key=lambda x:x[1])[1]-min(landmarks,key=lambda x:x[1])[1]
                size=round((x_range+y_range)/(width+height),2)                                  # size of hand relative to screen
                avx,avy=round(avx/len(handslms.landmark),1),round(avy/len(handslms.landmark),1) # average of all the hand
                avg_palm_x,avg_palm_y=round((palm[0]+avx)/2,1),round((palm[1]+avy)/2,1)         # average of the hand in relation to the palm
                dist_hand=distance(avg_palm_x,avg_palm_y,avx,avy)                               # distance of the thumb in relation to the palm
                
                # store last fifteen average x and y cooordinates
                if  avx != 0 and avy != 0:
                    avx_list.append(avx)
                    avy_list.append(avy)
                    size_list.append(size)
                if  len(avx_list) > 15:
                    avx_list.pop(0)
                    avy_list.pop(0)
                    size_list.pop(0)

                # setting a sensitivity for how much each finger is considered _R or not
                sensitivity = 0.6
                
                #index finger exists in the correct range to determine if the hand is in frame
                if  index_x[0]!=0:
                    thumb_R=(dist_hand<distance(thumb_x[0],thumb_y[0],avg_palm_x,avg_palm_y)*sensitivity)
                    index_R=(dist_hand<distance(index_x[0],index_y[0],avg_palm_x,avg_palm_y)*sensitivity)
                    middle_R=(dist_hand<distance(middle_x[0],middle_y[0],avg_palm_x,avg_palm_y)*sensitivity)
                    ring_R=(dist_hand<distance(ring_x[0],ring_y[0],avg_palm_x,avg_palm_y)*sensitivity)
                    pinky_R=(dist_hand<distance(pinky_x[0],pinky_y[0],avg_palm_x,avg_palm_y)*sensitivity)
                
                

                #print if fingers are _R or not
                cv2.putText(frame, 'Thumb _R: ' + str(thumb_R),  (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if thumb_R == True:thumbR = 1
                else:thumbR = 0
                cv2.putText(frame, 'Index _R: ' + str(index_R),  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if index_R == True:indexR = 1
                else:indexR = 0
                cv2.putText(frame, 'Middle _R: '+ str(middle_R), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if middle_R == True:middleR = 1
                else:middleR = 0
                cv2.putText(frame, 'Ring _R: '  + str(ring_R),   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if ring_R == True:ringR = 1
                else:ringR = 0
                cv2.putText(frame, 'Pinky _R: ' + str(pinky_R),  (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                if pinky_R == True:pinkyR = 1
                else:pinkyR = 0

                if index_R == False and middle_R == False and ring_R == False and pinky_R == False:isFist = True
                else:isFist = False
                
                if(setup_file["crashChrisComputer"]=="True"):index=0;mpDraw.draw_landmarks(frame,handslms,mpHands.HAND_CONNECTIONS) # Reset index, Drawing landmarks on frames
                    
                #reset index
                index = 0
        
        if result.multi_hand_landmarks:        
            last_landmarks = result.multi_hand_landmarks   
            countdown=0 
        
        # if the hand is in the frame
        if  len(avx_list) > 1:

            if(setup_file["mouseControl"] == "True"):mouse.move(int((avg_palm_x-200)*8-400), int((avg_palm_y-200)*4-400)) # move mouse to the center of the palm
            
            #is the hand in a held position?
            isHeld = (not index_R) and (not middle_R) and (not ring_R) and (not pinky_R)

            #check which quadrent the avg palm is
            if(avg_palm_x>0 and avg_palm_x<first_eighth_width):quadrent=1
            elif(avg_palm_x>first_eighth_width  and avg_palm_x<first_quarter_width):quadrent=2
            elif(avg_palm_x>first_quarter_width and avg_palm_x<last_quarter_width):quadrent=3
            elif(avg_palm_x>last_quarter_width  and avg_palm_x<last_eighth_width):quadrent=4
            elif(avg_palm_x>last_eighth_width):quadrent=5
            else:quadrent=0
            
            #show the quadrent the hand is in
            cv2.putText(frame,str(str(quadrent)+", "+str(avx)+", "+str(avy)+", "+str(isFist)),(100,100),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),1)
            if(setup_file["serialOutput"]=="True" and canSend):
                if  index_x[0]!=0 and setup_file["serialOutput"] == "True":ser.write(bytes('gesture' + '|' + str(quadrent) + '|' + str(round(avx)) + '|' + str(round(avy)) + '|' + str(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))) + '|' + str(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))+ '|' + str(indexR) + '|' + str(middleR) + '|' + str(ringR) + '|' + str(pinkyR) + '|' + str(isFist) + '\n', encoding='utf8'))
                canSend = False
            #show hand size
            cv2.putText(frame, 'size: ' + str(size),  (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1)
            
            if(setup_file["outputInTerminal"] == "True")and(index_x[0]!=0):print(str(str(quadrent) + ', ' + str(round(avx)) + ', ' + str(round(avy)) + ', ' + str(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))) + ', ' + str(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))) + ', ' + str(indexR) + ', ' + str(middleR) + ', ' + str(ringR) + ', ' + str(pinkyR) + ', ' + str(isFist)))#(quadrent, x-coord of hand, y-coord of hand, camera res width, camera res height, index finger _R, middle finger _R, ring finger _R, pinky finger _R, is fist?)

            #if the hand is not held
            if(setup_file["mouseControl"] == "True"):
                if  not isHeld:
                    if  mouse.is_pressed('left'):
                        mouse.release('left')
                        print("released")
                    elif not index_R:
                        mouse.click('left')
                        print("clicked")
                        time.sleep(0.25)
                    elif not pinky_R:
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
        #cv2.waitKey(100) #10 fps

        # Press q to quit
        if  cv2.waitKey(1) == ord('q'):
            if setup_file["serialOutput"] == "True":ser.close()
            break

    # release the webcam and destroy all active windows
    cap.release()

    # destroy all windows
    cv2.destroyAllWindows()

except serial.SerialException as e:
    print(str(e))
    if setup_file["serialOutput"] == "True":
        os.system('systemctl reboot -i')

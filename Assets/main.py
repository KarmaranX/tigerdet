import numpy as np
import cv2
import requests

from keras.applications.mobilenet import MobileNet
from keras.applications.mobilenet import preprocess_input
from keras.applications import imagenet_utils

mobile = MobileNet()
def prepare_image(img):
    img_resize = cv2.resize(img,(224,224))
    img_array_expanded_dims = np.expand_dims(img_resize, axis=0)
    return preprocess_input(img_array_expanded_dims)

bg_frame_cnt = 10
frame_cnt = 30*60

frame_width = 640 
frame_height = 360 

cap = cv2.VideoCapture(0)


if not cap.isOpened():
    print("Cannot read video")
    exit()

cnt = 0

bg_avg = np.zeros((frame_height,frame_width,3), dtype="uint8")

while True:
    cnt += 1
    if(cnt==frame_cnt): 
        cnt = 0
        bg_avg = np.zeros((frame_height,frame_width,3), dtype="uint8")

    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (frame_width, frame_height))
    cv2.imshow("Video_Feed", frame)
    
    if(cnt<bg_frame_cnt) :
        bg_avg+=(frame//bg_frame_cnt)
        # cv2.imshow("Back_AVG", bg_avg)
        continue

    subt = cv2.subtract(frame,bg_avg)
    blur = cv2.GaussianBlur(subt,(5,5),3)
    edged = cv2.Canny(blur, 250, 250) 
    (contours, _) = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)[:20]

    x_min = frame_width
    y_min = frame_height
    x_max = 0
    y_max = 0
   
    for x in contours:
        for y in x:
            for z in y:
                x_max = max(x_max,z[0])
                x_min = min(x_min,z[0])
                y_max = max(y_max,z[1])
                y_min = min(y_min,z[1])

    # add 20 px up down left right

    inc = 20
    x_max = min(x_max + inc, 1280)
    x_min = max(x_min - inc, 0)

    y_max = min(y_max + inc, 720)
    y_min = max(y_min - inc, 0)

    if (not(x_max <= x_min or y_max <= y_min)): # if image is empty
        # continue

        preprocessed_image = prepare_image(frame[y_min:y_max, x_min:x_max])
        predictions = mobile.predict(preprocessed_image)
        results = imagenet_utils.decode_predictions(predictions)
        print(results)
        conf = [i[2] for i in results[0] if 'tiger' in i[1]]

        print("this is the conf",conf)

        if conf:
            response = requests.get("http://localhost:8000/add/notifications")
            quit()

        
        if conf:
            cv2.drawContours(frame, contours, -1, (0, 0, 255), 3)
            cv2.rectangle(frame,(x_min, y_min),(x_max, y_max),(0,255,0),3)
            cv2.putText(frame, f"Tiger : {conf[0]*100:.2f}%", (x_min,y_min-5), cv2.FONT_HERSHEY_PLAIN, 1.5, (0,255,255), 2)

    cv2.imshow("Background_subtracted", subt)
    cv2.imshow("Edges", edged)

    cv2.imshow("Bounds",frame)
    
    cv2.waitKey(10)

    
cap.release()
cv2.destroyAllWindows()
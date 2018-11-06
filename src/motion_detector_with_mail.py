# USAGE
# python motion_detector.py
# python motion_detector.py --video videos/example_01.mp4

# import the necessary packages
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2

t_i = time.time()
###Part about mail###
import smtplib
#import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def SendMail(filename='',time=''):
    fromaddr = "RPi.8Me216@yahoo.com"
    toaddr = "banane329@gmail.com"
    passwd = "RPi_8Me216"
    
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Creenshot from RPi_Camera - Python email"
    
    body = "The Camera has detected something the : " + time
    msg.attach(MIMEText(body, 'plain'))
    attachment = open(filename, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(part)
    
    
    try :
        print("try to send the mail...")
        server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
        server.starttls()
        server.login(fromaddr, passwd)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
        print("email sent! \o/")
    except :
        print ("can't send the Email!  :/")
    





# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file", default="HDSurveillanceVideoSample.mp4")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())


# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
#    vs = cv2.VideoCapture('HDSurveillanceVideoSample.mp4')   
    vs =PiVideoStream(resolution=(320, 240), framerate=32)
    vs.start()
    time.sleep(2.0)

# otherwise, we are reading from a video file
else:
	vs = cv2.VideoCapture(args["video"])

# initialize the first frame in the video stream
#firstFrame = None
reference_frames_count = 5
reference_frames = [None, None, None, None, None]
frame_skip = 80
frame_num = -1

previous_time = time.time()-60
amount_frame = 0;

# loop over the frames of the video
while True:
	#increment frame number
	frame_num+=1

	# grab the current frame and initialize the occupied/unoccupied
	# text
	for i in range (5):
		frame = vs.read()
	frame = frame if args.get("video", None) is None else frame[1]
	text = "Unoccupied"

	# if the frame could not be grabbed, then we have reached the end
	# of the video
	if frame is None:
		break

	# resize the frame, convert it to grayscale, and blur it
	frame = imutils.resize(frame, width=500)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)

	# if the first frame is None, initialize it
	if frame_num % frame_skip == 0:
		reference_frames.pop()
		reference_frames.insert(0, gray)
		print(frame_num)
		continue

	contours = []
	for i in range(reference_frames_count):

		if(reference_frames[i] is None):
			continue
		# compute the absolute difference between the current frame and
		# first frame
		frameDelta = cv2.absdiff(reference_frames[i], gray)
		thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

		# dilate the thresholded image to fill in holes, then find contours
		# on thresholded image
		thresh = cv2.dilate(thresh, None, iterations=2)
		cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		contours.extend(cnts[0] if imutils.is_cv2() else cnts[1])

	rects = []
	# loop over the contours
	for c in contours:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < args["min_area"]:
			continue

		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		rects.append(cv2.boundingRect(c))

	num_rects = 50
	selected_rects = [[0 for i in range(num_rects)] for j in range(num_rects)]
	step = 20
	min_ocurrences = 4
	for i in range(num_rects):
		for j in range(num_rects):
			x_p = step/2 + j * step
			y_p = step/2 + i * step
			for r in rects:
				(x, y, w, h) = r
				if x_p >= x and x_p < x+w and y_p >= y and y_p < y+h:
				    	selected_rects[i][j] += 1
					
				    	if selected_rects[i][j] >= min_ocurrences:
				    	    x = j * step
				    	    y = i * step
				    	    w = step
				    	    h = step
				    	    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
				    	    text = "Occupied"
				    	    continue



	#selected_rects.count()

	# draw the text and timestamp on the frame
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

	# show the frame and record if the user presses a key
	cv2.imshow("Security Feed", frame)
#	cv2.imshow("Thresh", thresh)
#	cv2.imshow("Frame Delta", frameDelta)
#	cv2.imshow("bleus", reference_frames[0])
	# if reference_frames[2] is not None:
	# 	cv2.imshow("bleus2", reference_frames[2])
	# if reference_frames[4] is not None:
	# 	cv2.imshow("bleus4", reference_frames[4])

	key = cv2.waitKey(1) & 0xFF

	# if the `q` key is pressed, break from the lop
	if key == ord("q"):
		break
    
	if text == "Occupied":
		amount_frame+=1
	
		if amount_frame > 10 and time.time()-previous_time > 60: #Screenshot maximum every 60sec and only if 8 frames detect something
			now = str(datetime.datetime.now())
			cv2.imwrite(now + ".jpg", frame) #Screenshot
			previous_time = time.time()
			amount_frame = 0
			print('screenshot : ' + now)
			SendMail(now+".jpg",now)

	else:
		amount_frame-=1
    
	if amount_frame < 0:
		amount_frame = 0
    

#cleanup the camera and close any open windows
vs.stop() if args.get("video", None) is None else vs.release()
cv2.destroyAllWindows()
print("Execution time : ",time.time()-t_i)

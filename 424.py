"""
@author: Alkan, Cem, Kaan, Berke
"""

import email
import sys, os, time
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QErrorMessage, QMessageBox
from PyQt5 import QtGui, uic
from click import password_option
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mysql.connector
from mysql.connector import Error

path = 'People'
images = []
classNames = []
myList = os.listdir(path)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])


def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

def send_email(fromaddr, password, toaddr, className):
    # instance of MIMEMultipart
    msg = MIMEMultipart()
    
    # storing the senders email address  
    msg['From'] = fromaddr
    
    # storing the receivers email address 
    msg['To'] = toaddr
    
    # storing the subject 
    msg['Subject'] = "Attendance List of " + className
    
    # string to store the body of the mail
    body = "You can find the attendance list below."
    
    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))
    
    # open the file to be sent 
    filename = "Attendance.csv"
    attachment = open("./Attendance.csv", "rb")
    
    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')
    
    # To change the payload into encoded form
    p.set_payload((attachment).read())
    
    # encode into base64
    encoders.encode_base64(p)
    
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    
    # attach the instance 'p' to instance 'msg'
    msg.attach(p)
    
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
    
    # start TLS for security
    s.starttls()
    
    # Authentication
    s.login(fromaddr, password)
    
    # Converts the Multipart msg into a string
    text = msg.as_string()
    
    # sending the mail
    s.sendmail(fromaddr, toaddr, text)
    
    # terminating the session
    s.quit()
def markAttendance(name):
    with open('Attendance.csv', 'r+') as f:
        alreadyAttendant = f.readlines()
        nameList = []
        for line in alreadyAttendant:
            entry = line.split(',')
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')


encodeListKnown = findEncodings(images)
print('Encoding Completed')

qtCreatorFile = "424_gui.ui" # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QMainWindow, Ui_MainWindow):
    email = ""
    password = ""
    className = ""
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        # Asagidakiler errow windowu cikartmak icin istiyosan
        # self.msg = QMessageBox()
        # self.msg.setIcon(QMessageBox.Critical)
        # self.msg.setWindowTitle("Error")
        
        self.setupUi(self)
        
        # asagidaki gibi self.UIElementIsmi.connect(self.fonksiyonIsmi) ile assign edersin
        self.loginBtn.clicked.connect(self.login)
        self.logoutBtn.clicked.connect(self.logout)
        self.startBtn.clicked.connect(self.start)
        self.stopBtn.clicked.connect(self.stop)
    
    def login(self):
        try:
            connection = mysql.connector.connect(host='ilzyz0heng1bygi8.chr7pe7iynqr.eu-west-1.rds.amazonaws.com',
                                                database='roc41t4gzn28ruo9',
                                                user='ak6mk6wqk27shcuq',
                                                password='xsptey88l5m4fr12')
            if connection.is_connected():

                cursor = connection.cursor()
                cursor.execute("SELECT * FROM Instructor")
                instructors = cursor.fetchall()
                print("Instructors: ", instructors)
                email = self.emailInput.toPlainText()
                password = self.passInput.toPlainText()
                
                if email in [instructor[2] for instructor in instructors] and password in [instructor[3] for instructor in instructors]:
                    lgnMsg = "Logged in successfully as "+ email
                    self.loginMsg.setText(lgnMsg)
                else:
                    self.loginMsg.setText('Error')

        except Error as e:
            print("Error while connecting to MySQL", e)
            
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed")
    
    def logout(self):
        self.emailInput.setText("")
        self.passInput.setText("")
        self.loginMsg.setText('Logout Successfully')
        
    def start(self):
        self.label.setText('Started')
        cap = cv2.VideoCapture(0)

        while True:
            _, img = cap.read()
        
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        
            encodesCurFrame = face_recognition.face_encodings(imgS, face_recognition.face_locations(imgS))
        
            for encodeFace, faceLoc in zip(encodesCurFrame, face_recognition.face_locations(imgS)):
        
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)
        
                if faceDis[matchIndex] < 0.50:
                    name = classNames[matchIndex].upper()
                    markAttendance(name)
                else:
                    name = 'Unknown'
        
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
        
            cv2.imshow('Webcam', img)
            if cv2.waitKey(1)  & 0xff == ord('q'):
                break

    def stop(self):
        self.label.setText('Stopped')
        email = self.emailInput.toPlainText()
        className = self.classInput.toPlainText()
        try:
            send_email("ceng424iyte@gmail.com","ceng424iyte123", email, className)
        except:
            self.loginMsg.setText('Email cannot be sent. Check your email')
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

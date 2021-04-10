#-*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import re
import threading

import urllib
import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import pyperclip
import chromedriver_autoinstaller

'''
dirname = os.getcwd()
filename = os.path.join(dirname, '')
print(filename)
os.chdir(filename.decode('utf-8'))
try:
    os.system(os.path.join(filename, 'chromeDebuggingMode64Bit.bat'))
except:
    os.system(os.path.join(filename, 'chromeDebuggingMode32Bit.bat'))
'''

#time.sleep(3)
chromedriver_autoinstaller.install()
co = Options()
co.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=co)
"""
네이버 밴드에 글작성
"""

def login(id,pw):
    driver.find_element_by_class_name('uBtn.-icoType.-naver.externalLogin').click()

    """
    네이버 로그인
    """
    user_id = driver.find_element_by_id("id")
    password = driver.find_element_by_id("pw")
    time.sleep(1)

    user_id.click()
    pyperclip.copy(id)
    user_id.send_keys(Keys.CONTROL, 'v')
    time.sleep(1)

    password.click()
    pyperclip.copy(pw)
    password.send_keys(Keys.CONTROL, 'v')
    time.sleep(1)

    password.submit()

def write_board(str):
    driver.find_element_by_class_name('cPostWriteEventWrapper._btnOpenWriteLayer').click()
    time.sleep(5)
    driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div/div/section/div/div/div/div[2]/div').click()
    driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div/div/section/div/div/div/div[2]/div/p').send_keys(str)
    driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div/div/section/div/div/div/div[3]/div/div[2]/button').click()
    time.sleep(3)

def macro(id, pw, urls, content, count):
    print(count,'번째 매크로 실행 중...')
    for url in urls:
        driver.get(url)
        time.sleep(3)

        if driver.current_url != url:
            login(id,pw)

        time.sleep(5)
        write_board(content)
    print(count,"번째 매크로 실행 완료!")

def getBandList(id, pw):
    print('가입된 밴드 목록 가져오는 중...')
    driver.get('https://band.us/my/profiles')
    time.sleep(3)

    if driver.current_url != 'https://band.us/my/profiles':
        login(id,pw)
    
    bandListSize = len(driver.find_elements_by_xpath('//*[@id="content"]/section/div[2]/section/ul/*'))
    
    bandList = list()
    for i in range(1, bandListSize+1):
        name = driver.find_element_by_xpath(f'//*[@id="content"]/section/div[2]/section/ul/li[{i}]/span[2]').text.strip()
        url = driver.find_element_by_xpath(f'//*[@id="content"]/section/div[2]/section/ul/li[{i}]').get_attribute('data-band-no')
        bandList.append({'name':name,'url':'https://band.us/band/'+url})

    return bandList

class MacroThread(QThread):
    finished_event = pyqtSignal()
    def __init__(self, id, pw, urls, content, parent=None):
        super().__init__()
        self.id = id
        self.pw = pw
        self.urls = urls.split(',')
        self.content = content
        self.count = 0
 
    def run(self):
        macro(self.id, self.pw, self.urls, self.content, self.count)
        self.finished_event.emit()

class IntervalThread(QThread):
    def __init__(self, id, pw, urls, delay, content, parent=None):
        QThread.__init__(self, parent)
        self.delay = delay
        self.count = 0
        self.macroThread = MacroThread(parent=self, id=id, pw=pw, urls=urls, content=content)
        self.macroThread.finished_event.connect(self.finished)

    def run(self):
        self.startMacro()

    def startMacro(self):
        self.count+=1
        self.macroThread.count = self.count
        self.macroThread.start()

    def stop(self):
        self.macroThread.terminate()

    @pyqtSlot()
    def finished(self):
        QTimer.singleShot(int(self.delay)*1000, self.startMacro)
        

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.intialL1 = '아이디'
 
        self.intialL2 = '비밀번호'
        
        self.intialL3 = '밴드주소(,로 구분)'
        
        self.intialL4 = '딜레이(초)'
        
        self.intialL5 = '내용'
 
        Layout = QGridLayout()
 
        self.setLayout(Layout)
 
        labelobj1 = QLabel(self.intialL1,self)
 
        Layout.addWidget(labelobj1,0,0)
 
        labelobj2 = QLabel(self.intialL2, self)
 
        Layout.addWidget(labelobj2, 1, 0)
        
        labelobj3 = QLabel(self.intialL3, self)
 
        Layout.addWidget(labelobj3, 2, 0)

        labelobj4 = QLabel(self.intialL4, self)
 
        Layout.addWidget(labelobj4, 3, 0)

        labelobj5 = QLabel(self.intialL5, self)
 
        Layout.addWidget(labelobj5, 4, 0)
 
        self.idEdit = QLineEdit(self)
 
        self.idEdit.textChanged.connect(self.validateText)

        Layout.addWidget(self.idEdit,0,1)
 
        #idEdit.textChanged.connect(lambda:self.print_label(idEdit,labelobj1))
 
        self.pwEdit = QLineEdit(self)

        self.pwEdit.textChanged.connect(self.validateText)
 
        #self.pwEdit.setEchoMode(2)
 
        Layout.addWidget(self.pwEdit, 1, 1)
 
        #pwEdit.textChanged.connect(lambda: self.print_label(pwEdit, labelobj2))
 
        self.urlsEdit = QLineEdit(self)

        combinedText = ""
        for band in getBandList('chad0706', 'asdf0706'):
            combinedText += band['url']+','
        combinedText = combinedText[:-1]

        self.urlsEdit.setText(combinedText)

        self.urlsEdit.textChanged.connect(self.validateText)

        #self.urlsEdit.setValidator(QRegExpValidator(QRegExp("https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)?(,)?"),self))
 
        Layout.addWidget(self.urlsEdit,2,1)

        self.delayEdit = QLineEdit(self)

        self.delayEdit.setValidator(QIntValidator(self))

        self.delayEdit.textChanged.connect(self.validateText)
 
        Layout.addWidget(self.delayEdit,3,1)

        self.contentEdit = QPlainTextEdit(self)

        self.contentEdit.textChanged.connect(self.validateText)
 
        Layout.addWidget(self.contentEdit,4,1)

        self.StartButton = QPushButton(self)
        self.StartButton.setText("시작")
        self.StartButton.clicked.connect(self.startInterval)
        self.StartButton.setEnabled(False)
        Layout.addWidget(self.StartButton, 5,0)

        self.StopButton = QPushButton(self)
        self.StopButton.setText("종료")
        self.StopButton.clicked.connect(self.stopInterval)
        self.StopButton.setEnabled(False)
        Layout.addWidget(self.StopButton, 5,1)

        self.setWindowTitle('네이버 밴드 글쓰기 매크로')
        self.setGeometry(300, 300, 600, 400)
        self.show()

    def validateText(self):
        enabled = True
        if self.idEdit.text() == "" or self.pwEdit.text() == "" or self.urlsEdit.text() == "" or self.delayEdit.text() == "" or self.contentEdit.toPlainText() == "":
            enabled = False

        elif not bool(re.match(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)?(,)?",self.urlsEdit.text())):
            enabled = False

        elif int(self.delayEdit.text())<10:
            enabled=False
        
        self.StartButton.setEnabled(enabled)
        
    def startInterval(self):
        self.intervalTask = IntervalThread(parent=self, id=self.idEdit.text(), pw=self.pwEdit.text(), urls=self.urlsEdit.text(), delay=self.delayEdit.text(), content=self.contentEdit.toPlainText())
        self.intervalTask.start()
        self.StartButton.setEnabled(False)
        self.StopButton.setEnabled(True)

    def stopInterval(self):
        self.intervalTask.stop()
        self.intervalTask.terminate()
        self.StartButton.setEnabled(True)
        self.StopButton.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())

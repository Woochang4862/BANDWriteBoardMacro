import urllib
import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import pyperclip
import chromedriver_autoinstaller

chromedriver_autoinstaller.install()
co = Options()
co.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
driver = webdriver.Chrome(options=co)

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

def write_board(content, image=r"C:\Users\wooch\OneDrive\바탕 화면\ss.png"):
    driver.find_element_by_class_name('cPostWriteEventWrapper._btnOpenWriteLayer').click()
    time.sleep(5)
    driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div/div/section/div/div/div/div[2]/div').click()
    driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div/div/section/div/div/div/div[2]/div/p').send_keys(content)
    driver.find_element_by_xpath('/html/body/div[1]/div[3]/div/div/section/div/div/div/div[3]/ul/li[1]/label/input').send_keys(image)
    time.sleep(3)
    driver.find_element_by_xpath('//*[@id="wrap"]/div[3]/div[2]/div/section/div/footer/button[2]').click()
    time.sleep(3)
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

macro('chad0706', 'asdf0706', ['https://band.us/band/83539360'], '#테스트', 1)
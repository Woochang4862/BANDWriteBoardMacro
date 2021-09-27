from typing_extensions import final
from selenium.webdriver.support.ui import *
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, NoAlertPresentException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import time
import logging
from datetime import datetime, timedelta

from DriverProvider import setup_driver
from LoginMacro import LOGIN_IDENTIFICATION, loginWithEmail, LOGIN_ERROR, LOGIN_SUCCESS, LOGGED_IN
from DBHelper import *

from PyQt5.QtCore import *

logger = logging.getLogger()
FORMAT = "[%(asctime)s][%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logger.setLevel(logging.INFO)

WAIT_SECONDS = 10

"""
디버깅 변수
"""
ID = "chand0706@naver.com"
PW = "asdf070612"
IP = None
CONTENT = r"테스트 글"
RSRV_DATE = "2021-08-08"
RSRV_TIME = "오전 9:00"
RSRV_INTERVAL = 15
RSRV_NUMBER = 30
DELAY = 10

class WriteBoardRestrictionBandException(Exception):
    def __str__(self):
        return "글을 작성 할 수 없는 밴드"

class ReservationRestrictionBandException(Exception):
    def __str__(self):
        return "예약을 할 수 없는 밴드"

class WriteBoardThread(QThread):

    id = ''
    pw = ''
    ip = ''
    content = ''
    band_list = ''

    number_of_rsrv = 30
    start_datetime = ''
    interval = 0
    delay = 0

    on_finished_write_board = pyqtSignal()
    on_update_progressbar = pyqtSignal(int)
    on_error_write_board = pyqtSignal(str, str) # 발생한 밴드, 오류 메시지

    on_logging_info_write_board = pyqtSignal(str, str)
    on_logging_warning_write_board = pyqtSignal(str, str)
    on_logging_error_write_board = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__()

    def run(self):
        self.isRunning = True
        self.on_logging_info_write_board.emit("글쓰기 매크로",f"{self.ip}로 아이피 변경 및 드라이버 준비 중 ...")
        self.driver = setup_driver(self.ip)
        self.on_logging_info_write_board.emit("글쓰기 매크로",f"{self.ip}로 아이피 변경 및 드라이버 준비 완료")
        self.on_logging_info_write_board.emit("글쓰기 매크로",f"{self.id}로 로그인 시도 중 ...")
        result = loginWithEmail(self.driver, self.id, self.pw)
        if result == LOGIN_SUCCESS or result == LOGGED_IN:
            self.on_logging_info_write_board.emit("글쓰기 매크로",f"{self.id}로 로그인 성공!")
            try:
                start = datetime.strptime(self.start_datetime.replace("오전", "AM").replace("오후", "PM"), "%Y%m%d %p %I:%M")

                rsrv_datetimes = []

                for _ in range(self.number_of_rsrv):
                    rsrv_datetimes.append((start.strftime("%Y%m%d"), start.strftime("%p %I:%M").replace(" 0", " ").replace("AM", "오전").replace("PM", "오후")))
                    start += timedelta(minutes=self.interval)

                logging.info(f"밴드 목록 : {self.band_list}")
                logging.info(f"예약할 시간 : {rsrv_datetimes}")
                progress = 0
                for band_id in self.band_list:
                    self.on_logging_info_write_board.emit("글쓰기 매크로",f"{band_id}에 예약 글쓰는 중 ...")
                    cnt = 0
                    for rsrv_datetime in rsrv_datetimes:
                        self.on_logging_info_write_board.emit("글쓰기 매크로",f"{band_id}에 {rsrv_datetime[0]+' '+rsrv_datetime[1]}로 글쓰는 중 ...")
                        try:
                            self.write_board(self.driver, band_id, self.content, rsrv_datetime[0], rsrv_datetime[1], self.delay)
                            self.on_logging_info_write_board.emit("글쓰기 매크로",f"{band_id}에 {rsrv_datetime[0]+' '+rsrv_datetime[1]}로 글쓰기 완료됨")
                            progress += 1
                            cnt += 1
                            self.on_update_progressbar.emit(((progress/(len(self.band_list)*len(rsrv_datetimes)))*100))
                        except UnexpectedAlertPresentException:
                            self.on_logging_error_write_board.emit("글쓰기 매크로",f"{band_id}에 {rsrv_datetime[0]+' '+rsrv_datetime[1]}에서 예약글 한도 수 초과됨!")
                            progress -= cnt
                            progress += self.number_of_rsrv
                            self.on_update_progressbar.emit(((progress/(len(self.band_list)*len(rsrv_datetimes)))*100))
                            break
                        except WriteBoardRestrictionBandException:
                            self.on_logging_error_write_board.emit("글쓰기 매크로",f"{band_id}에는 게시글을 올릴 수 없습니다")
                            progress += self.number_of_rsrv
                            self.on_update_progressbar.emit(((progress/(len(self.band_list)*len(rsrv_datetimes)))*100))
                            break
                        except ReservationRestrictionBandException:
                            self.on_logging_error_write_board.emit("글쓰기 매크로",f"{band_id}에는 예약글을 올릴 수 없습니다")
                            progress += self.number_of_rsrv
                            self.on_update_progressbar.emit(((progress/(len(self.band_list)*len(rsrv_datetimes)))*100))
                            break      
                self.on_finished_write_board.emit()

            except:
                logging.exception("")
        else:
            self.on_logging_error_write_board.emit("글쓰기 매크로",f"{self.id}로 로그인 실패!")

    def stop(self):
        try:
            self.isRunning = False
            self.quit()
            self.driver.close()
            self.driver.quit()
        except Exception:
            logging.exception("")

    def write_board(self, driver, band_id, content, date, _time, delay):
        wait = WebDriverWait(driver, WAIT_SECONDS)

        try:
            driver.get(f'https://band.us/band/{band_id}')
        except UnexpectedAlertPresentException:
            raise

        self.on_logging_info_write_board.emit("글쓰기 매크로", f"'글쓰기'버튼 클릭")
        try:
            write_board_btn = wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="cPostWriteEventWrapper _btnOpenWriteLayer"]'))
            )
            write_board_btn.click()
        except TimeoutException:
            raise WriteBoardRestrictionBandException()
            
        self.on_logging_info_write_board.emit("글쓰기 매크로", f"글 입력 중 ...")
        content_editor_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[starts-with(@class, "contentEditor _richEditor skin")]'))
        )
        content_editor_btn.click()

        content_editor = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[starts-with(@class, "contentEditor _richEditor skin") and contains(@class, "cke_editable cke_editable_inline cke_contents_ltr")]/p'))
        )
        content_editor.send_keys(content)
        self.on_logging_info_write_board.emit("글쓰기 매크로", f"글 입력 완료!")

        self.on_logging_info_write_board.emit("글쓰기 매크로", f"예약 시간 설정 중 ...")
        write_setting_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="btnSetting _btnWriteSetting"]'))
        )
        write_setting_btn.click()

        try:
            notice_radio = wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="notice"]'))
            )
            notice_radio.click()

            reserve_btn = wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="reserve"]'))
            )
            reserve_btn.click()
        except TimeoutException:
            raise ReservationRestrictionBandException()

        self.on_logging_info_write_board.emit("글쓰기 매크로", f"예약 글 날짜 : {date}")
        date_picker = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id, "view") and contains(@id, "pickedDate")]'))
        )
        date_picker.click()
        date_picker.send_keys(Keys.CONTROL, 'a')
        date_picker.send_keys(Keys.BACKSPACE)
        date_picker.send_keys(date)
        date_picker.send_keys(Keys.ENTER)
        self.on_logging_info_write_board.emit("글쓰기 매크로", f"날짜 입력 완료!")

        self.on_logging_info_write_board.emit("글쓰기 매크로", f"예약 글 시간 : {_time}")
        time_picker = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[starts-with(@id, "view") and contains(@id, "_pickedDateTime")]'))
        )
        time_picker.click()

        time_item = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//*[@data-time="{_time}"]'))
        )
        ActionChains(driver).move_to_element(time_item).click(time_item).perform()
        self.on_logging_info_write_board.emit("글쓰기 매크로", f"시간 입력 완료!")
        self.on_logging_info_write_board.emit("글쓰기 매크로", f"예약 시간 설정 완료!")

        done_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="uButton -confirm _btnComplete"]'))
        )
        done_btn.click()

        reserve_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="uButton -sizeM _btnSubmitPost -confirm"]'))
        )
        reserve_btn.click()

        self.on_logging_info_write_board.emit("글쓰기 매크로", f"{delay}초를 기다리는 중...")
        time.sleep(delay)
        self.on_logging_info_write_board.emit("글쓰기 매크로", f"딜레이 수행 완료!")

class GetBandListThread(QThread):

    id = ''
    pw = ''
    ip = ''

    on_finished_get_band_list = pyqtSignal(list)
    on_error_get_band_list = pyqtSignal(str) # 오류 메시지

    on_logging_info_get_band_list = pyqtSignal(str, str)
    on_logging_warning_get_band_list = pyqtSignal(str, str)
    on_logging_error_get_band_list = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__()

    def run(self):
        self.isRunning = True
        self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{self.ip}로 아이피 변경 및 드라이버 준비 중 ...")
        self.driver = setup_driver(self.ip)
        self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{self.ip}로 아이피 변경 및 드라이버 준비 완료")
        self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{self.id}로 로그인 시도 중 ...")
        result = loginWithEmail(self.driver, self.id, self.pw)
        if result == LOGIN_SUCCESS or result == LOGGED_IN:
            self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{self.id}로 로그인 성공!")
            self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{self.id}의 밴드 목록 불러오는 중 ...")
            try:
                band_list = self.getBandList(self.driver)
                self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{self.id}의 밴드 목록 블러오기 완료!")
                self.on_finished_get_band_list.emit(band_list)
            except:
                logging.exception("")
        else:
            self.on_logging_error_get_band_list.emit("글쓰기 매크로",f"{self.id}로 로그인 실패!")
        
        self.driver.close()
        self.driver.quit()

    def stop(self):
        try:
            self.isRunning = False
            self.quit()
            self.driver.close()
            self.driver.quit()
        except Exception:
            logging.exception("")

    def getBandList(self, driver):
        wait = WebDriverWait(driver, WAIT_SECONDS)

        driver.get("https://band.us/my/profiles")

        result = []

        bands = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, f'//*[@class="bandList _bands"]/li'))
        )
        self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{len(bands)}개의 밴드 정보 불러오는 중 ...")
        for band in bands:
            band_id = band.get_attribute('data-band-no')
            title = band.text
            self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"밴드 아이디 : {band_id}, 이름 : {title}")
            result.append((int(band_id), title, f'https://band.us/band/{band_id}'))
        self.on_logging_info_get_band_list.emit("밴드 목록 불러오기",f"{len(bands)}개의 밴드 정보 불러오기 완료!")

        return result
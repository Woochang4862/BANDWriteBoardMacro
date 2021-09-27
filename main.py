from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

import sys
import logging
import time
import os
from datetime import datetime, timedelta

from WriteBoardMacro import WriteBoardThread, GetBandListThread
from LoginMacro import ValidateAccountThread
from DBHelper import *

logger = logging.getLogger()
FORMAT = "[%(asctime)s][%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logging.basicConfig(format=FORMAT, filename=f'./log/{time.strftime("%Y-%m-%d")}.log')
logger.setLevel(logging.INFO)

form_class = uic.loadUiType(os.path.abspath("./ui/write_board_macro.ui"))[0]

class MyWindow(QMainWindow, form_class):

    """
    시그널
    ::START::
    """
    state_validation_finished = pyqtSignal()
    state_identification_finished = pyqtSignal()
    """
    ::END::
    """

    """
    변수
    ::START::
    """
    bands = []
    selected_bands = []
    isRunning = False
    """
    ::END::
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowIcon(QIcon('icon.ico'))

        """
        스레드
        ::START::
        """
        self.validateAccountThread = ValidateAccountThread(parent=self)
        self.validateAccountThread.state_logged_in.connect(self.state_logged_in)
        self.validateAccountThread.state_login_success.connect(self.state_login_success)
        self.validateAccountThread.state_login_fail.connect(self.state_login_fail)
        self.validateAccountThread.state_login_error.connect(self.state_login_error)
        self.validateAccountThread.state_login_validation.connect(self.state_login_validation)
        self.validateAccountThread.state_login_identification.connect(self.state_login_identification)

        self.getBandListThread = GetBandListThread(parent=self)
        self.getBandListThread.on_finished_get_band_list.connect(self.on_finished_get_band_list)
        self.getBandListThread.on_error_get_band_list.connect(self.on_error_get_band_list)
        self.getBandListThread.on_logging_info_get_band_list.connect(self.loggingInfo)
        self.getBandListThread.on_logging_warning_get_band_list.connect(self.loggingWarning)
        self.getBandListThread.on_logging_error_get_band_list.connect(self.loggingError)
        """
        ::END::
        """

        self.rsrv_interval_edit.setValidator(QIntValidator(self))
        self.delay_edit.setValidator(QIntValidator(self))

        connect()
        _id = getStringExtra(KEY_ID, "")
        pw = getStringExtra(KEY_PW, "")
        ip = getStringExtra(KEY_IP, "")
        content = getStringExtra(KEY_CONTENT, "")
        rsrv_interval = getStringExtra(KEY_RSRV_INTERVAL, "")
        delay = getStringExtra(KEY_DELAY, "")
        rsrv_datetime = getStringExtra(KEY_RSRV_DATETIME, "")
        self.bands = getBands()
        close()
        
        self.id_edit.setText(_id)
        self.pw_edit.setText(pw)
        self.ip_edit.setText(ip)
        self.content_edit.setPlainText(content)
        self.rsrv_interval_edit.setText(rsrv_interval)
        self.delay_edit.setText(delay)
        self.rsrv_datetime_edit.setDateTime(QDateTime.fromString(rsrv_datetime,'yyyyMMdd AP h:mm'))

        self.bindToBandList()
        self.validateRunButton()

    """
    계정 설정
    ::START::
    """
    def on_id_editing_finished(self):
        text = self.id_edit.text()
        connect()
        text_on_db = getStringExtra(KEY_ID, "")
        close()
        if text == text_on_db:
            return
        logging.info(text)
        connect()
        putStringExtra(KEY_ID, text)
        putIntegerExtra(KEY_ACCOUNT_VALIDATION, 0)
        close()
        self.validateRunButton()

    def on_pw_editing_finished(self):
        text = self.pw_edit.text()
        connect()
        text_on_db = getStringExtra(KEY_PW, "")
        close()
        if text == text_on_db:
            return
        logging.info(text)
        connect()
        putStringExtra(KEY_PW, text)
        putIntegerExtra(KEY_ACCOUNT_VALIDATION, 0)
        close()
        self.validateRunButton()

    def on_ip_editing_finished(self):
        text = self.ip_edit.text()
        connect()
        text_on_db = getStringExtra(KEY_IP, "")
        close()
        if text == text_on_db:
            return
        logging.info(text)
        connect()
        putStringExtra(KEY_IP, text)
        putIntegerExtra(KEY_ACCOUNT_VALIDATION, 0)
        close()
        self.validateRunButton()

    def on_validation_account_clicked(self):
        logging.info("계정 확인")
        if self.isRunning:
            return
        id = self.id_edit.text().strip()
        pw = self.pw_edit.text().strip()
        ip = self.ip_edit.text().strip()

        if id != '' and pw != '':
            self.validateAccountThread.id = id
            self.validateAccountThread.pw = pw
            self.validateAccountThread.ip = ip
            self.validateAccountThread.start()
        else:
            logging.info("계정 확인 : 이메일 혹은 비밀번호가 비어 있음")

    def on_band_browse_clicked(self):
        logging.info("밴드 불러오기")
        if self.isRunning:
            return
        id = self.id_edit.text().strip()
        pw = self.pw_edit.text().strip()
        ip = self.ip_edit.text().strip()
        self.getBandListThread.id = id
        self.getBandListThread.pw = pw
        self.getBandListThread.ip = ip
        self.getBandListThread.start()

    def on_finished_get_band_list(self, band_list):
        logging.info(f"밴드 불러오기 결과 : {band_list}")
        if self.isRunning:
            return
        self.selected_bands.clear()
        connect()
        clearBands()
        for band in band_list:
            addBand(*band)
        self.bands = getBands()
        close()
        self.bindToBandList()

    def on_error_get_band_list(self, msg):
        self.loggingError("밴드 불러오기", msg)

    @pyqtSlot()
    def state_logged_in(self):
        self.loggingInfo("계정 확인", f"밴드에 이미 로그인 되어있는 계정이 있습니다")
        QMessageBox.warning(self.centralwidget, '로그인 상태', '로그아웃 후 다시 시도해 주세요', QMessageBox.Ok, QMessageBox.Ok)
        connect()
        putIntegerExtra(KEY_ACCOUNT_VALIDATION, 0)
        close()

    @pyqtSlot()
    def state_login_success(self):
        self.loggingInfo("계정 확인", f"{self.id}는 유효한 계정입니다")
        QMessageBox.information(self.centralwidget, '로그인 성공', '밴드 정보를 불러와주세요', QMessageBox.Ok, QMessageBox.Ok)
        connect()
        putIntegerExtra(KEY_ACCOUNT_VALIDATION, 1)
        close()

    @pyqtSlot()
    def state_login_fail(self):
        self.loggingInfo("계정 확인", f"{self.id}는 유효하지 않은 계정입니다")
        QMessageBox.critical(self, '로그인 실패', '이메일 또는 비밀번호를 확인해 주세요', QMessageBox.Ok, QMessageBox.Ok)
        connect()
        putIntegerExtra(KEY_ACCOUNT_VALIDATION, 0)
        close()

    @pyqtSlot()
    def state_login_error(self):
        self.loggingInfo("계정 확인", f"{self.id}로 로그인하던 중 오류 발생했습니다")
        QMessageBox.critical(self, '로그인 오류', '로그인 시도 중 문제가 발생하였습니다', QMessageBox.Ok, QMessageBox.Ok)
        connect()
        putIntegerExtra(KEY_ACCOUNT_VALIDATION, 0)
        close()

    @pyqtSlot()
    def state_login_validation(self):
        self.loggingInfo("계정 확인", f"{self.id}에서 이메일 인증을 필요로 합니다")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("이메일 인증 후 아래 확인 버튼을 눌러 주세요")
        msgBox.setWindowTitle("이메일 인증 요청")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.buttonClicked.connect(lambda _ : self.state_validation_finished.emit())
        msgBox.exec()

    @pyqtSlot()
    def state_login_identification(self):
        self.loggingInfo("계정 확인", f"{self.id}에서 본인확인을 필요로 합니다")
        new_pw, ok = QInputDialog.getText(self, 'IP 변경 감지됨', '본인확인 후 변경된 비밀번호를 입력해주세요')

        if ok:
            self.pw_edit.setText(new_pw)
            self.state_identification_finished.emit()
    """
    ::END::
    """

    """
    밴드 설정
    ::START::
    """
    def bindToBandList(self):
        self.band_list_view.clear()
        self.selected_bands.clear()

        for band_id, name, url, checked in self.bands: # 사용자정의 item 과 checkbox widget 을, 동일한 cell 에 넣어서 , 추후 정렬 가능하게 한다. 
            item = QListWidgetItem()
            item.setData(Qt.DisplayRole, name)
            item.setData(Qt.ToolTipRole, f"{name}({band_id})")
            item.setData(Qt.UserRole, band_id)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.band_list_view.addItem(item) 
            if checked:
                self.selected_bands.append(band_id)

        self.band_list_view.setSortingEnabled(False)  # 정렬기능
        self.band_list_view.itemChanged.connect(self.on_band_list_item_changed)

        logging.info(f"계정 로딩 : {len(self.bands)} 개가 로딩됨")
        self.loggingInfo("계정 로딩", f"{len(self.bands)} 개가 로딩됨")

    def on_band_list_item_changed(self, item:QListWidgetItem):
        if item.checkState() == Qt.Checked and not item.data(Qt.UserRole) in self.selected_bands:
            self.selected_bands.append(item.data(Qt.UserRole))
            connect()
            updateBandChecked(item.data(Qt.UserRole), 1)
            close()
        elif item.checkState() == Qt.Unchecked and item.data(Qt.UserRole) in self.selected_bands:
            self.selected_bands.remove(item.data(Qt.UserRole))
            connect()
            updateBandChecked(item.data(Qt.UserRole), 0)
            close()

        logging.info(f"밴드 체크 변경 : {self.selected_bands}")
        self.loggingInfo(f"밴드 체크 변경", f"{len(self.selected_bands)}개의 밴드가 체크됨")

        self.validateRunButton()
    """
    ::END::
    """

    """
    내용 설정
    ::START::
    """
    def on_content_changed(self):
        text = self.content_edit.toPlainText()
        logging.info(text)
        connect()
        text_on_db = getStringExtra(KEY_CONTENT, "")
        close()
        if text == text_on_db:
            return

        connect()
        putStringExtra(KEY_CONTENT, text)
        close()

        self.validateRunButton()
    """
    ::END::
    """

    """
    탭 설정
    ::START::
    """
    def on_tab_changed(self, index):
        if self.isRunning:
            return
        logging.info(f"선택된 탭 : {index}")
        if index == 0:
            connect()
            self.bands = getBands()
            close()
            self.bindToBandList()
        elif index == 1:
            pass
        elif index == 2:
            pass

    """
    ::END::
    """

    """
    예약 관련 변수 설정
    ::START::
    """
    def on_rsrv_datetime_edited(self):
        connect()
        text_on_db = getStringExtra(KEY_RSRV_DATETIME, "")
        close()
        if self.rsrv_datetime_edit.dateTime().toString('yyyyMMdd AP h:mm') == text_on_db:
            return
        logging.info(f"예약 날짜 변경됨 : {self.rsrv_datetime_edit.dateTime()}")
        connect()
        putStringExtra(KEY_RSRV_DATETIME, self.rsrv_datetime_edit.dateTime().toString('yyyyMMdd AP h:mm'))
        close()
        self.validateRunButton()

    def on_interval_editing_finished(self):
        text = self.rsrv_interval_edit.text()
        connect()
        text_on_db = getStringExtra(KEY_RSRV_INTERVAL, "")
        close()
        if text == text_on_db:
            return
        logging.info(f"예약 시간 간격 변경됨 : {text}")
        connect()
        putStringExtra(KEY_RSRV_INTERVAL, text)
        close()
        self.validateRunButton()

    def on_delay_editing_finished(self):
        text = self.delay_edit.text()
        connect()
        text_on_db = getStringExtra(KEY_DELAY, "")
        close()
        if text == text_on_db:
            return
        connect()
        putStringExtra(KEY_DELAY, text)
        close()
        self.validateRunButton()

    """
    ::END::
    """

    """
    실행/중단 설정
    ::START::
    """
    def on_run_clicked(self):
        logging.info("실행")

        id = self.id_edit.text().strip()
        pw = self.pw_edit.text().strip()
        ip = self.ip_edit.text().strip()

        content = self.content_edit.toPlainText().strip(' \n')
        start_datetime = self.rsrv_datetime_edit.dateTime()
        interval = int(0 if self.rsrv_interval_edit.text().strip() == "" else self.rsrv_interval_edit.text().strip())
        delay = int(0 if self.delay_edit.text().strip() == "" else self.delay_edit.text().strip())

        logging.info(f"현재 실행 환경 (이메일 : {id}, 비밀번호 : {pw}, 아이피 : {ip}, 밴드 : {self.selected_bands}, 내용 : {content}, 예약날짜 : {start_datetime.toString('yyyyMMdd AP h:mm')})")

        self.toggleRunButton(False)
        self.toggleStopButton(True)

        self.isRunning = True

        self.progressBar.reset()
        self.progressBar.setValue(0)

        self.writeBoardThread = WriteBoardThread(parent=self)
        self.writeBoardThread.on_finished_write_board.connect(self.on_finished_write_board)
        self.writeBoardThread.on_update_progressbar.connect(self.on_update_progressbar)
        self.writeBoardThread.on_logging_info_write_board.connect(self.loggingInfo)
        self.writeBoardThread.on_logging_warning_write_board.connect(self.loggingWarning)
        self.writeBoardThread.on_logging_error_write_board.connect(self.loggingError)
        self.writeBoardThread.id = id
        self.writeBoardThread.pw = pw
        self.writeBoardThread.ip = ip
        self.writeBoardThread.content = content
        self.writeBoardThread.start_datetime = start_datetime.toString('yyyyMMdd AP h:mm')
        self.writeBoardThread.band_list = self.selected_bands
        self.writeBoardThread.interval = interval
        self.writeBoardThread.delay = delay
        self.writeBoardThread.start()

    def on_stop_clicked(self):
        logging.info("중단")
        if self.writeBoardThread.isRunning:
            self.writeBoardThread.stop()
        self.isRunning = False
        self.toggleStopButton(False)
        self.toggleRunButton(True)

    def validateRunButton(self):
        connect()
        self.isValidate = getIntegerExtra(KEY_ACCOUNT_VALIDATION, 0)
        close()

        start_datetime = self.rsrv_datetime_edit.dateTime().toPyDateTime()
        interval = int(0 if self.rsrv_interval_edit.text().strip() == "" else self.rsrv_interval_edit.text().strip())

        diff: timedelta = datetime.now() - start_datetime

        logging.info(f"계정 유효성 : {self.isValidate}, 선택된 밴드 : {len(self.selected_bands)}, 내용 : {self.content_edit.toPlainText().strip()}, 현재 시간과 차이 : {diff.microseconds}")
        self.loggingInfo("실행 가능 유무 검사", f"=====================================================")
        self.loggingInfo("실행 가능 유무 검사", f"계정 유효성 : {bool(self.isValidate)}")
        self.loggingInfo("실행 가능 유무 검사", f"선택된 밴드 : {len(self.selected_bands)}개")
        self.loggingInfo("실행 가능 유무 검사", f"내용 : \n{self.content_edit.toPlainText().strip()}")
        self.loggingInfo("실행 가능 유무 검사", f"예약 시작 시간 유효성 : {start_datetime.minute%5 == 0}")
        self.loggingInfo("실행 가능 유무 검사", f"간격 유효성 : {interval%5 == 0}")
        self.loggingInfo("실행 가능 유무 검사", f"현재 시간과 차이 : {diff.total_seconds()/1000} 초")
        self.loggingInfo("실행 가능 유무 검사", f"=====================================================")

        if self.isValidate and len(self.selected_bands) != 0 and self.content_edit.toPlainText().strip() != "" and diff.total_seconds() < -60 and start_datetime.minute%5 == 0 and interval%5 == 0:
            self.toggleRunButton(True)
        else:
            self.toggleRunButton(False)

    def toggleRunButton(self, enabled=None):
        if enabled is None:
            self.run_btn.setEnabled(not self.run_btn.isEnabled())
        else:
            self.run_btn.setEnabled(enabled)

    def toggleStopButton(self, enabled=None):
        if enabled is None:
            self.stop_btn.setEnabled(not self.stop_btn.isEnabled())
        else:
            self.stop_btn.setEnabled(enabled)

    def on_update_progressbar(self, value):
        self.progressBar.setValue(value)

    def on_finished_write_board(self):
        self.on_stop_clicked()
        self.validateRunButton()

    def on_error_write_board(self, band_id, msg):
        logging.info(f"{id}에서 {msg}")

        # if msg == "한도 수 초과":
        #     self.on_stop_clicked()
        #     self.validateRunButton()
    """
    ::END::
    """

    """
    작업상황(로그) 설정
    ::START::
    """
    def loggingInfo(self, action, msg):
        currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_view.append(f"[{currentTime}] {action} - <b>{msg}</b>")

    def loggingError(self, action, msg):
        currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_view.append(f'<p style="color: red"><b>[{currentTime}] {action} - <i>{msg}</i></b></p>') 

    def loggingWarning(self, action, msg):
        currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_view.append(f'<p style="color: grey">[{currentTime}] {action} - <b>{msg}</b></p>') 
    """
    ::END::
    """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
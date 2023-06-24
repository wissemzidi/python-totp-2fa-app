from pyperclip import copy as copy_text
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from sys import exit as sys_exit
from PyQt5.uic import loadUi
from time import sleep
import threading
import datetime
import pyotp
import json
import os


def init_otp():
    global otp_names, otp_tokens
    otp_names = []
    with open("session.json", "r") as f:
        if not (f.readable()) or os.path.getsize("session.json") == 0:
            fen.curr_otp.setText("otp not found !")
            return

        data = json.loads(f.read())
        otp_array = data["otp_tokens"]
        otp_names = [otp_name for otp_name in otp_array]
        otp_tokens = [otp_array[otp_token] for otp_token in otp_array]

        global show_current_otp_thread
        show_current_otp_thread = threading.Thread(
            target=show_current_otp, daemon=True
        ).start()


def add_otp():
    # try:
    new_otp_token = fen.new_otp_token.text()
    new_otp_name = fen.new_otp_name.text()

    if len(new_otp_token) != 32:
        fen.new_otp_token.setText("Not valid otp token !")
        return

    if not 2 < len(new_otp_name) < 30:
        fen.new_otp_token.setText("Not valid otp name !")
        return

    if os.path.getsize("session.json") > 0:
        with open("session.json", "r") as f:
            old_data = json.loads(f.read())["otp_tokens"]
    else:
        old_data = {}

    with open("session.json", "w") as f:
        if not f.writable():
            fen.new_otp_token.setText("the json file isn't writable !")
            return

        new_session_data = {"otp_tokens": {**old_data, new_otp_name: new_otp_token}}
        if not new_otp_name in old_data:
            global current_page_i
            current_page_i = len(old_data)

        f.write(json.dumps(new_session_data))
        fen.new_otp_token.setText("otp added successfully ✅")
        fen.new_otp_name.setText("")

    global otp
    otp = init_otp()

    load_pages_buttons()  # todo => fixing it
    # except Exception: # ! undo comment in production
    #     fen.new_otp_token.setText("An Error happened !")
    #     return


def show_current_otp():
    otp = pyotp.TOTP(otp_tokens[current_page_i])
    current_otp_name = otp_names[current_page_i]
    while True:
        time_remaining = int(
            otp.interval - datetime.datetime.now().timestamp() % otp.interval
        )
        fen.curr_otp.setText(otp.now())
        fen.current_otp_name.setText(current_otp_name)
        while time_remaining > 0:
            fen.otp_timeCounter.setText(str(time_remaining))
            # fen.otp_timeBar.setValue(time_remaining)  # ? idk why it throw an error
            time_remaining -= 1
            sleep(1)
        sleep(1)


def load_pages_buttons():
    if len(otp_names) == 0:
        return

    # todo and to fix :)
    for i in range(len(otp_names)):
        page_btn = QtWidgets.QPushButton(text=str(otp_names[i]), parent=fen.otp_pages)
        page_btn.setCursor(QCursor(Qt.CursorShape(13)))
        page_btn.setObjectName = f"otp_page{i}"
        page_btn.clicked.connect(lambda: changePage(i))
        page_btn.move(0, 50 * (i + 1))
        page_btn.setStyleSheet("margin-top: 20px;")


def changePage(i):
    global current_page_i, show_current_otp_thread

    current_page_i = i
    show_current_otp_thread = threading.Thread(
        target=show_current_otp, daemon=True
    ).start()


# todo => fix the deleting from the arrays
def delete_otp():
    global otp_names, otp_tokens

    deleted_otp_name = fen.new_otp_name.text()

    if not deleted_otp_name in otp_names:
        return

    delete_otp_index = otp_names.index(deleted_otp_name)
    otp_names.remove(deleted_otp_name)
    otp_tokens.remove(otp_tokens[delete_otp_index])

    with open("session.json", "w") as f:
        new_data = json.dumps(
            {"otp_tokens": {otp_names[i]: otp_tokens[i] for i in range(len(otp_names))}}
        )
        f.write(new_data)

    changePage(0)
    load_pages_buttons()


def copy_otp():
    otp = pyotp.TOTP(otp_tokens[current_page_i])
    copy_text(otp.now())
    fen.copy_btn.setText("COPIED")
    threading.Thread(target=reset_copy_text, daemon=True).start()


def reset_copy_text():
    sleep(4)
    fen.copy_btn.setText("COPY")


#
#
######### Main program #########


App = QtWidgets.QApplication([])
App.setWindowIcon(QtGui.QIcon("MY2FA.png"))

fen = loadUi("main_interface.ui")
fen.setWindowTitle("MY2FA")

global current_page_i
current_page_i = 0

otp = init_otp()
load_pages_buttons()

fen.addOtp_btn.clicked.connect(add_otp)
fen.copy_btn.clicked.connect(copy_otp)
fen.deleteOtp_btn.clicked.connect(delete_otp)
# fen.btn_page0.clicked.connect(change_page)

fen.show()
App.exec()
sys_exit(App.exit())

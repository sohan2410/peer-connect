#   create simple GUI using PyQt5

# step 1: import pyqt5 module
# step 2: define a method
# step 3: define method for title
# displaying application using show method
# main method to run application

import sys

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox, QLineEdit, QHBoxLayout, QDesktopWidget, QMainWindow, QLabel, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt
import qdarktheme
import socket
import errno
import sys
import threading
import logging
import time
import os
import tqdm

from utils.sockets import get_ip

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s - Line %(lineno)d', level=logging.DEBUG)

thread_lock = threading.Lock()

HEADER_LENGTH = 10

IP = get_ip()
PORT = 1234


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "Welcome to peer connect center"

        # self.left = 10
        # self.right = 10
        self.width = 320
        self.height = 200
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.setGeometry(0, 0, self.width, self.height)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        button = QPushButton("Continue", self)
        # button.setToolTip(self.title)
        # button.move(120, 70)
        button.setFixedWidth(150)
        # import pyqtslot to pass onclick function in connect
        button.clicked.connect(self.openNewWindow)
        hbox = QHBoxLayout()

        self.textbox = QLineEdit(self)
        # self.textbox.move(60, 30)
        self.textbox.setFixedWidth(240)
        self.textbox.resize(200, 30)
        self.textbox.setPlaceholderText("Enter username")
        hbox.addWidget(self.textbox)
        hbox.addWidget(button)

        layout.addLayout(hbox)
        self.center()

        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def openNewWindow(self):
        username = self.textbox.text()
        if not username:
            QMessageBox.question(self, 'Message ',
                                 "please Enter a Username", QMessageBox.Ok, QMessageBox.Ok)

        # Change the title of the current window
        else:

            # Remove the button and textbox
            self.new_window = QMainWindow()
            self.new_window.setWindowTitle("Welcome  <" + username + ">")
            self.new_window.setGeometry(50, 50, self.width, self.height)

            central_widget = QWidget()
            self.new_window.setCentralWidget(central_widget)

            layout = QVBoxLayout(central_widget)
            layout.setAlignment(Qt.AlignCenter)

            message_label = QLabel("Enter a message:", central_widget)
            self.message_textbox = QLineEdit(central_widget)
            self.message_textbox.setFixedWidth(240)
            self.message_textbox.setPlaceholderText("Enter message")

            send_button = QPushButton("Send Message", central_widget)
            # send_button.clicked.connect(self.sendMessage)

            layout.addWidget(message_label)
            layout.addWidget(self.message_textbox)
            layout.addWidget(send_button)

            self.new_window.show()
            self.close()  # Close the current window

        # self.textbox.move(60, 30)

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            client_socket.connect((IP, PORT))


# client_socket.setblocking(False)

            myusername = username.encode('utf-8')
            username_header = f"n{len(myusername):<{HEADER_LENGTH-1}}".encode('utf-8')
            client_socket.send(username_header + myusername)
            threading.Thread(target=self.connectToServer,
                             args=(client_socket,)).start()

    @pyqtSlot()
    def onclick(self):
        print("button clicked")
        username = self.textbox.text()

        print(username)
        # self.close()

    def connectToServer(self, client_socket):
        while True:
            print("hello")
            try:
                username_header = client_socket.recv(HEADER_LENGTH)
                print(username_header)
                if not len(username_header):
                    print('Connection closed by the server')
                    sys.exit()
                username_length = int(
                    username_header.decode('utf-8').strip()[1:])
                username = client_socket.recv(username_length).decode('utf-8')
                message_header = client_socket.recv(HEADER_LENGTH)
                message_type = chr(message_header[0])
                message_length = int(
                    message_header.decode('utf-8').strip()[1:])
                message = client_socket.recv(message_length).decode('utf-8')
                if message_type == 'F':
                    pass
                else:

                    with thread_lock:
                        print('\n' + f'{username} > {message}')

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    logging.error("An exception occurred at line %d: %s",
                                  e.__traceback__.tb_lineno, e, exc_info=True)
                    sys.exit()
            # continue

            except Exception as e:
                logging.error("An exception occurred at line %d: %s",
                              e.__traceback__.tb_lineno, e, exc_info=True)
                sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()

    ex = App()
    sys.exit(app.exec_())

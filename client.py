import socket
import errno
import sys
import threading
import logging
import time
import os
import tqdm

from utils.sockets import get_ip
from utils.helpers import find_in_dict

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s - Line %(lineno)d', level=logging.DEBUG)


HEADER_LENGTH = 10

IP = get_ip()
PORT = 1234
my_username = input("Username: ")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 0x06)
client_socket.connect((IP, PORT))

client_send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_send_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
client_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 0x06)
client_send_socket.connect((IP, PORT))

# connected = [client_recv_socket]


username = my_username.encode('utf-8')
username_header = f"n{len(username):<{HEADER_LENGTH-1}}".encode('utf-8')
client_socket.sendall(username_header + username)
client_send_socket.sendall(username_header + username)


def on(client_socket):
    while True:
        try:
            username_header = client_socket.recv(HEADER_LENGTH)
            if not len(username_header):
                print('Connection closed by the server')
                sys.exit()
            username_length = int(username_header.decode('utf-8').strip()[1:])
            username = client_socket.recv(username_length).decode('utf-8')
            message_header = client_socket.recv(HEADER_LENGTH)
            message_type = chr(message_header[0])
            message_length = int(message_header.decode(
                'utf-8').strip().split('_')[0][1:])
            message = client_socket.recv(message_length).decode('utf-8')
            if message_type == 'F':
                pass
            else:
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


threading.Thread(target=on, args=(client_socket,)).start()


def send_message(message, username=None):
    message_header = f"M{len(message):<{HEADER_LENGTH-1}}".encode('utf-8')
    if (username):
        message_type = "P"+str(len(message))+"_"+username
        message_header = '{:<{}}'.format(
            message_type, HEADER_LENGTH).encode('utf-8')
    message = message.encode('utf-8')
    client_socket.sendall(message_header + message)


def send_file(filename):
    try:
        file_size = os.path.getsize(filename)
        print(file_size)
        with open(filename, 'rb') as file:
            message_header = f"F{file_size:<{HEADER_LENGTH-1}}".encode('utf-8')
            client_send_socket.sendall(message_header)
            client_send_socket.sendfile(file)
    except Exception as e:
        logging.error("An exception occurred at line %d: %s",
                      e.__traceback__.tb_lineno, e, exc_info=True)


while True:
    message = input(f'{my_username} > ')
    if message:
        if message == 'file':
            filename = input('Enter the name of the file: ')
            threading.Thread(target=send_file, args=(filename,)).start()
        elif message == '1':
            username = input("Enter the username: ")
            text = input('Enter the text: ')
            threading.Thread(target=send_message,
                             args=(text, username,)).start()

        else:
            threading.Thread(target=send_message, args=(message,)).start()

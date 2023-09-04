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
my_username = input("Username: ")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((IP, PORT))

# client_socket.setblocking(False)

username = my_username.encode('utf-8')
username_header = f"n{len(username):<{HEADER_LENGTH-1}}".encode('utf-8')
client_socket.send(username_header + username)


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
            message_length = int(message_header.decode('utf-8').strip()[1:])
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


threading.Thread(target=on, args=(client_socket,)).start()


def send_message(message):
    message = message.encode('utf-8')
    message_header = f"M{len(message):<{HEADER_LENGTH-1}}".encode('utf-8')
    client_socket.send(message_header + message)


def send_file(filename):
    try:
        file_size = os.path.getsize(filename)
        progress = tqdm.tqdm(range(
            file_size), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, 'rb') as file:
            message_header = f"F{file_size:<{HEADER_LENGTH-1}}".encode('utf-8')
            client_socket.send(message_header)
            while True:
                data = file.read(1024)
                if not data:
                    break
                client_socket.send(data)
                progress.update(len(data))

    except Exception as e:
        logging.error("An exception occurred at line %d: %s",
                      e.__traceback__.tb_lineno, e, exc_info=True)


while True:
    message = input(f'{my_username} > ')
    if message:
        if message == 'file':
            filename = input('Enter the name of the file: ')
            threading.Thread(target=send_file, args=(filename,)).start()
        else:
            threading.Thread(target=send_message, args=(message,)).start()
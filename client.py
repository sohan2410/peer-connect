import socket
import errno
import sys
import threading
import logging
import time

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s - Line %(lineno)d', level=logging.DEBUG)

print_lock = threading.Lock()

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = input("Username: ")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((IP, PORT))

client_socket.setblocking(False)

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
                print('File received from client...')
                filename = './tmp/'+str(int(time.time()))+'.txt'
                fo = open(filename, 'w')
                while message:
                    if not message:
                        break
                    else:
                        fo.write(message)
                        message_length -= len(message)
                        message = client_socket.recv(
                            min(message_length, 1024)).decode('utf-8')
                fo.close()
            else:
                with print_lock:
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

            # print('Reading error: '.format(str(e)))
            sys.exit()


threading.Thread(target=on, args=(client_socket,)).start()

while True:
    message = input(f'{my_username} > ')
    if message:

        if message == 'file':
            filename = input('Enter the name of the file: ')
            try:
                file = open(filename, 'r')
                file_data = file.read()
                if not file_data:
                    break
                while file_data:
                    message = str(file_data).encode('utf-8')
                    message_header = f"F{len(message):<{HEADER_LENGTH-1}}".encode(
                        'utf-8')
                    client_socket.send(message_header + message)
                    file_data = file.read()
                file.close()
            except Exception as e:
                logging.error("An exception occurred at line %d: %s",
                              e.__traceback__.tb_lineno, e, exc_info=True)

        else:
            message = message.encode('utf-8')
            message_header = f"M{len(message):<{HEADER_LENGTH-1}}".encode(
                'utf-8')
            client_socket.send(message_header + message)

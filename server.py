import socket
import select
import logging
import time
import threading
from utils.sockets import get_ip
from utils.helpers import find_in_dict
import os
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s - Line %(lineno)d', level=logging.DEBUG)

HEADER_LENGTH = 10

IP = get_ip()
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 0x06)
server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]
data = []
clients = {}

print(f'Listening for connections on {IP}:{PORT}')


def receive_file(client_socket, message_length):
    try:
        filename = './tmp/' + str(int(time.time())) + '.txt'
        received = 0
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            while received != message_length:
                new_data = client_socket.recv(message_length)
                if not new_data:
                    break
                received += len(new_data)
                f.write(new_data)
                f.flush()
        print('File received:', filename)
        return True
    except Exception as e:
        logging.error(f'Error in receive_file: {e}')
        return False


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        # if not len(message_header):
        #     return False

        # if len(message_header) < HEADER_LENGTH:
        #     return False

        # Extract the message length from the header
        # 'P5_username     '
        message_length_str = message_header.decode(
            'utf-8').strip().split('_')[0][1:]
        if not message_length_str.isdigit():
            return None

        message_length = int(message_length_str)
        message_type = message_header.decode('utf-8').strip().split('_')[0][0]
        if message_type == 'F':
            recieve_file_thread = threading.Thread(
                target=receive_file, args=(client_socket, message_length))
            recieve_file_thread.start()
            return None
        if message_type == 'P':
            username = message_header.decode('utf-8').strip().split('_')[1]
            return {'header': message_header, 'data': client_socket.recv(message_length), 'type': 'P', 'username': username}
        else:
            return {'header': message_header, 'data': client_socket.recv(message_length)}

    except Exception as e:
        logging.error("An exception occurred at line %d: %s",
                      e.__traceback__.tb_lineno, e, exc_info=True)
        return None


while True:
    read_sockets, _, exception_sockets = select.select(
        sockets_list, [], sockets_list)
    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()
            user = receive_message(client_socket)
            if user is False:
                continue
            sockets_list.append(client_socket)
            clients[client_socket] = user
            # print(client_socket)
            # data.append(
            #     {'username': user['data'].decode('utf-8'), 'ipaddr': client_address, 'socket': client_socket, 'status': 'online'})
            print('Accepted new connection from {}:{}, username: {}'.format(
                *client_address, user['data'].decode('utf-8')))
        else:
            message = receive_message(notified_socket)
            if message is None:
                continue
            if message is False:
                print('Closed connection from: {}'.format(
                    clients[notified_socket]['data'].decode('utf-8')))
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            else:
                if 'type' in message and message['type'] == 'P':
                    to_send = find_in_dict(
                        data, 'username', message['username'])
                    to_send['socket'].send(
                        user["header"] + user["data"] + message["header"] + message["data"])
                else:
                    user = clients[notified_socket]
                    print(
                        f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
                    for client_socket in clients:
                        if client_socket != notified_socket:
                            try:
                                client_socket.send(
                                    user["header"] + user["data"] + message["header"] + message["data"])
                            except Exception as e:
                                logging.error("An exception occurred at line %d: %s",
                                              e.__traceback__.tb_lineno, e, exc_info=True)

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]

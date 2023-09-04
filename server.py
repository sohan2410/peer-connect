import socket
import select
import logging
import time
import threading
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s - Line %(lineno)d', level=logging.DEBUG)

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]
clients = {}

print(f'Listening for connections on {IP}:{PORT}')



def receive_file(client_socket,message_length):
    try:
        filename = './tmp/' + str(int(time.time())) + '.txt'
        received = 0
        data = b""
        with open(filename, "wb") as f:
                while received != message_length:
                    new_data = client_socket.recv(message_length)
                    if not len(new_data):
                        break
                    data += new_data
                    received += len(new_data)
                f.write(data)
                f.flush()
    except Exception as e:
        logging.error(f'Error in receive_file: {e}')
        return False 
           

def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode('utf-8').strip()[1:])
        message_type = message_header.decode('utf-8').strip()[0]
        if message_type == 'F':
            recieve_file_thread=threading.Thread(target=receive_file,args=(client_socket,message_length))
            recieve_file_thread.start()
        else:
         return {'header': message_header, 'data': client_socket.recv(message_length)}

    except Exception as e:
        logging.error(f'Error in receive_message: {e}')
        return False


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
                user = clients[notified_socket]
                print(
                    f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
                for client_socket in clients:
                    if client_socket != notified_socket:
                        try:
                            client_socket.send(
                                user["header"] + user["data"] + message["header"] + message["data"])
                        except Exception as e:
                            print("error", e)

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]

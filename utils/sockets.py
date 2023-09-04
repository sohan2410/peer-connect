import socket


def get_ip():
    try:
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
    except Exception:
        IPAddr = "127.0.0.1"
    return IPAddr


print(get_ip())

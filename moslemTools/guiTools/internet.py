import socket

def check_internet(timeout=1.0):
    for host in (("8.8.8.8", 53), ("1.1.1.1", 53)):
        try:
            sock = socket.create_connection(host, timeout=timeout)
            sock.close()
            return True
        except OSError:
            continue
    try:
        import requests
        requests.head("https://www.google.com", timeout=timeout)
        return True
    except Exception:
        return False

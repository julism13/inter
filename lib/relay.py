from lib.constants import TIMEOUT, MAX_RETRIES, LENGTH_PACKET
import socket


def extend_wait(client, message, ip, port, verbose, seq, end):
    timeout_global = 0
    client.settimeout(TIMEOUT)
    while timeout_global < MAX_RETRIES:
        try:
            client.sendto(message, (ip, port))
            if verbose == 1:
                print(f"[SEND] packet: {seq}"
                      f"| end_flag: {end}")

            packet, server_address = client.recvfrom(LENGTH_PACKET)
            return True
        except socket.timeout:
            timeout_global += 1
            if verbose == 1:
                print(f"The receiver is not responding, trying"
                      f" again (attempt {timeout_global}/{MAX_RETRIES})")

    return False

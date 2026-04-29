from lib.args_parser import parse_download
from lib.relay import extend_wait
from lib.constants import LENGTH_PACKET, END_FLAG, \
                          OPERATION_DOWNLOAD, SAW_PROTOCOL, SR_PROTOCOL
from lib.selective_repeat import manage_receiver_window_sr
import socket
import time


def selective_repeat_download(operation, seq, end, data, ip,
                              port, file_path, file_name, protocol,
                              verbose, client):
    conection_message = (f"{protocol}|{operation}|{file_name}"
                         f"|{seq:02d}|{end}|").encode('utf-8')
    packet = conection_message + data.encode('utf-8')

    if not extend_wait(client, packet, ip, port, verbose, seq, end):
        print("ERROR: Could not connect to the server")
        return

    expected_seq = 0
    data_buffer = {}
    client.settimeout(10.0)

    with open(file_path, 'wb') as file:
        while True:
            try:
                packet, server_address = client.recvfrom(LENGTH_PACKET)
            except socket.timeout:
                print(f"[SR] Global Timeout from {server_address} in upload."
                      f" Connection loss.")
                break
            keep_going, expected_seq = manage_receiver_window_sr(
                                            packet,
                                            client,
                                            server_address,
                                            expected_seq,
                                            file, data_buffer, verbose)

            if not keep_going:
                break

    client.close()
    print("[SR] File download successfully!")


'''------------------------------------------------------------------------'''


def receive_data_from_transmitter(client, seq, file, verbose):
    while True:
        packet, server_address = client.recvfrom(LENGTH_PACKET)
        parts = packet.split(b'|', 5)
        seq_from_server = int(parts[3].decode())
        end = int(parts[4].decode())
        data = parts[5]

        if verbose == 1:
            print(f"[RECV] Packet {seq_from_server} received."
                  f" Expected: {seq}")

        if seq != seq_from_server:
            if verbose == 1:
                print("[DROP] incorrect seq")
            return

        if end == END_FLAG:
            if verbose == 1:
                print("[FINISH] end_flag detected")

            client.sendto(str(seq_from_server).encode(), server_address)
            file.close()
            client.close()
            return

        file.write(data)

        if verbose == 1:
            print(f"[ACK] sending ACK: {seq_from_server}")

        client.sendto(str(seq_from_server).encode(), server_address)

        seq = 1 - seq


def stop_and_wait_dowload(operation, seq, end, data, ip,
                          port, file_path, file_name,
                          protocol, verbose, client):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = (f"{protocol}|{operation}|{file_name}"
               f"|{seq}|{end}|").encode('utf-8')
    packet = message + data.encode('utf-8')

    if not extend_wait(client, packet, ip, port, verbose, seq, end):
        print("ERROR: Could not connect to the server")
        return

    client.settimeout(None)

    file = open(file_path, 'wb')

    receive_data_from_transmitter(client, seq, file, verbose)

    file.close()

    print("[SAW] File downloaded successfully!")


def main():
    start_time = time.perf_counter()
    tokens = parse_download()
    operation = OPERATION_DOWNLOAD
    seq = 0
    end = 0
    data = ""
    ip = tokens[0]
    port = tokens[1]
    file_path = tokens[2]
    file_name = tokens[3]
    protocol = tokens[4]
    verbose = 1 if tokens[5] is True else 0
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if tokens[4] == SAW_PROTOCOL:
        stop_and_wait_dowload(operation, seq, end, data, ip, port,
                              file_path, file_name, protocol,
                              verbose, client)
    elif tokens[4] == SR_PROTOCOL:
        selective_repeat_download(operation, seq, end, data, ip,
                                  port, file_path, file_name, protocol,
                                  verbose, client)
        end_time = time.perf_counter()
        duration = end_time - start_time
        minutos, segundos = divmod(duration, 60)
        print(f"Tiempo total: {int(minutos):02d}:{int(segundos):02d}")
        print(f"Transferencia completada en: {duration:.4f} segundos")


main()

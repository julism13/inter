from lib.args_parser import parse_server
from lib.constants import LENGTH_PACKET, END_FLAG, TIMEOUT, MAX_RETRIES, \
                          WINDOW_SIZE, MAX_SEQ, OPERATION_UPLOAD, \
                          OPERATION_DOWNLOAD, SAW_PROTOCOL, \
                          SR_PROTOCOL, TIME_LISTEN_SOCKET
from lib.selective_repeat import load_data_in_buffer_sr, \
                                 send_packet_to_receiver_sr, \
                                 relay_no_ack_packet_to_receiver_sr, \
                                 manage_receiver_window_sr
from lib.stop_and_wait import assemble_packet
import socket
import os
import threading
import queue

# FEATURES:
# TODO Empezar a estrucutrar el README
# TODO Decidir qué será verbose y que no (prints por pantalla)
# TODO Modularizar
# TODO Pasarle al servidor el tamaño del archivo y que lo valide

# COMANDO (NO BORRAR):
# python3 start-server.py -H 0.0.0.0 -p 8080 -s ./archivos -v


def parse_packet(packet):
    parts = packet.split(b'|', 5)
    protocol = parts[0].decode()
    operation = parts[1].decode()
    file_name = parts[2].decode()
    seq = int(parts[3].decode())
    end = int(parts[4].decode())
    data = parts[5]
    return protocol, operation, file_name, seq, end, data


def exec_download_sr(server, client_address, client_queue,
                     first_packet, file_storage, active_sessions, verbose):
    protocol, operation, file_name, seq_receiver, _, _ = (
        parse_packet(first_packet))
    destination_path = os.path.join(file_storage, file_name)

    if verbose == 1:
        print(f"\n[NEW SESSION] Download SR started from {client_address}")
        print(f"[FILE] Serving file: {destination_path}")

    server.sendto(str(seq_receiver).encode(), client_address)

    if not os.path.exists(destination_path):
        print(f"[ERROR] The file was not found in: {file_name}"
              f"from {client_address}")

        delete_session(active_sessions, client_address)

        return

    buffer_data = []
    send_base = 0
    next_seq_num = 0
    no_ack_packets = {}

    header_size = len((f"{protocol}|{operation}"
                       f"|{file_name}|00|0|").encode('utf-8'))
    load_data_in_buffer_sr(destination_path, header_size, buffer_data)

    if not buffer_data:
        buffer_data = [b'']

    while send_base < len(buffer_data):
        while (
            next_seq_num < send_base + WINDOW_SIZE
            and next_seq_num < len(buffer_data)
        ):
            send_packet_to_receiver_sr(server, client_address, protocol,
                                       operation, file_name, next_seq_num,
                                       verbose, buffer_data, no_ack_packets)
            next_seq_num += 1

        try:
            ack_packet = client_queue.get(timeout=TIME_LISTEN_SOCKET)
            ack_seq = int(ack_packet.decode('utf-8'))
            if verbose == 1:
                print(f"[RECV] Received ACK for Seq: {ack_seq}")

            if ack_seq in no_ack_packets:
                del no_ack_packets[ack_seq]

            while (
                (send_base % MAX_SEQ) not in no_ack_packets
                and send_base < next_seq_num
            ):
                send_base += 1

            while True:
                try:
                    ack_packet = client_queue.get_nowait()
                    ack_seq = int(ack_packet.decode('utf-8'))
                    if ack_seq in no_ack_packets:
                        del no_ack_packets[ack_seq]
                    while (
                        (send_base % MAX_SEQ) not in no_ack_packets
                        and send_base < next_seq_num
                    ):
                        send_base += 1
                except queue.Empty:
                    break

        except queue.Empty:
            pass

        relay_no_ack_packet_to_receiver_sr(server, client_address, protocol,
                                           operation, file_name, verbose,
                                           buffer_data, no_ack_packets)

    if verbose == 1:
        print(f"[SR] Download from {client_address} successfully!")

    delete_session(active_sessions, client_address)


'''------------------------------------------------------------------------'''


def delete_session(active_sessions, client_address):
    if client_address in active_sessions:
        del active_sessions[client_address]
        print(f"Connection completed and cleaned for {client_address}")


def exec_upload_sr(server, client_address, client_queue,
                   first_packet, file_storage, active_sessions, verbose):
    if not os.path.exists(file_storage):
        os.makedirs(file_storage)

    _, _, file_name, _, _, _ = parse_packet(first_packet)

    destination_path = os.path.join(file_storage, file_name)
    expected_seq = 0
    data_buffer = {}

    if verbose == 1:
        print(f"\n[NEW SESSION] Upload SR started from {client_address}")
        print(f"[FILE] Destination: {destination_path}")

    client_queue.put(first_packet)

    with open(destination_path, 'wb') as file:
        while True:
            try:
                packet = client_queue.get(timeout=10.0)
                keep_going, expected_seq = manage_receiver_window_sr(
                                           packet,
                                           server,
                                           client_address,
                                           expected_seq, file,
                                           data_buffer, verbose)
                if not keep_going:
                    if verbose == 1:
                        print(f"[FINISH] End flag "
                              f"detected from {client_address}")
                    break

            except queue.Empty:
                print(f"[SR] Global Timeout from {client_address} in upload."
                      f" Connection loss.")
                break

    if verbose == 1:
        print(f"[SR] Upload from {client_address} successfully!")

    delete_session(active_sessions, client_address)


'''------------------------------------------------------------------------'''


def exec_upload_saw(server, client_address, client_queue, first_packet,
                    file_storage, active_sessions, verbose):

    if not os.path.exists(file_storage):
        os.makedirs(file_storage)

    _, _, file_name, seq, end, data = parse_packet(first_packet)

    destination_path = os.path.join(file_storage, file_name)
    expected_seq = 0

    if verbose == 1:
        print(f"\n[NEW SESSION] Upload SAW started from {client_address}")
        print(f"[FILE] Writing to: {destination_path}")

    with open(destination_path, 'wb') as file:
        if seq == expected_seq:
            if verbose:
                print(f"[RECV] First packet received. Seq: {seq}.")

            if end != END_FLAG:
                file.write(data)

            if verbose == 1:
                print(f"[ACK] sending ACK: {seq}")
            server.sendto(str(seq).encode(), client_address)
            expected_seq = 1 - expected_seq

            if end == END_FLAG:
                if verbose == 1:
                    print(f"[FINISH] end_flag detected "
                          f"in first packet from {client_address}")
                return

        while True:
            packet = client_queue.get()
            _, _, _, seq, end, data = parse_packet(packet)

            if verbose == 1:
                print(f"[RECV] packet {seq} received."
                      f" Expected: {expected_seq}")

            if seq == expected_seq:
                if end == END_FLAG:
                    if verbose == 1:
                        print(f"[FINISH] end_flag detected from "
                              f"{client_address}")
                    server.sendto(str(seq).encode(), client_address)
                    break

                file.write(data)

                if verbose == 1:
                    print(f"[ACK] sending ACK: {seq}")

                server.sendto(str(seq).encode(), client_address)
                expected_seq = 1 - expected_seq
            else:
                if verbose == 1:
                    print("[DROP] incorrect seq")
                continue

    if verbose == 1:
        print(f"[SAW] Upload from {client_address} successfully!")

    delete_session(active_sessions, client_address)


def exec_download_saw(server, client_address, client_packet_queue,
                      first_packet, file_storage, active_sessions, verbose):
    protocol, operation, file_name, seq, _, _ = parse_packet(
                                                         first_packet)
    destination_path = os.path.join(file_storage, file_name)

    server.sendto(str(seq).encode(), client_address)

    if not os.path.exists(destination_path):
        print(f"[{client_address}] [ERROR]: The file was not found in: "
              f"{destination_path}")
        return

    with open(destination_path, 'rb') as file:
        while True:
            packet, result = assemble_packet(file, protocol, operation,
                                             file_name, seq)

            if not result:
                break

            timeout_global = 0
            ack_received = False

            while timeout_global < MAX_RETRIES:
                server.sendto(packet, client_address)
                try:
                    ack_packet = client_packet_queue.get(timeout=TIMEOUT)
                    ack_seq = int(ack_packet.decode('utf-8'))
                    if verbose == 1:
                        print(f"[SEND] packet: {seq} | seq_abs: "
                              f"{ack_seq} | end_flag: 0")

                    if ack_seq == seq:
                        ack_received = True
                        seq = 1 - seq
                        break
                except queue.Empty:
                    timeout_global += 1
                    print(f"[{client_address}] Retrying to send package "
                          f"({timeout_global}/5)...")

            if not ack_received:
                print(f"[{client_address}] Connection lost "
                      f"during downloading.")
                return

    data = ""
    end_packet = (f"{protocol}|{operation}|{file_name}"
                  f"|{seq}|{END_FLAG}|{data}").encode('utf-8')
    timeout_global = 0
    while timeout_global < MAX_RETRIES:
        server.sendto(end_packet, client_address)
        if verbose == 1:
            print(f"[SEND] packet: {seq} | seq_abs: "
                  f"{ack_seq} | end_flag: 1")
        try:
            client_packet_queue.get(timeout=TIMEOUT)
            break
        except queue.Empty:
            timeout_global += 1

    if verbose == 1:
        print(f"[SAW] Download from {client_address} successfully!")

    delete_session(active_sessions, client_address)


def clients_threads(funtion, server, client_address, client_packets_queue,
                    packet, file_storage, active_sessions, verbose):
    client_thread = threading.Thread(
        target=funtion,
        args=(server, client_address, client_packets_queue, packet,
              file_storage, active_sessions, verbose)
    )
    client_thread.start()


def main():
    tokens = parse_server()
    ip = tokens[0]
    port = tokens[1]
    file_storage = tokens[2]
    verbose = 1 if tokens[3] is True else 0
    active_sessions = {}

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((ip, port))

    if verbose == 1:
        print(f"Server listening on {ip}:{port}...")

    while True:
        packet, client_address = server.recvfrom(LENGTH_PACKET)

        if client_address in active_sessions:
            active_sessions[client_address].put(packet)

        else:
            parts = packet.split(b'|', 6)
            protocol = parts[0].decode()
            operation = parts[1].decode()

            if verbose == 1:
                print(f"New client detected: {client_address} ({operation})")

            client_packets_queue = queue.Queue()
            active_sessions[client_address] = client_packets_queue

            if protocol == SAW_PROTOCOL:
                if operation == OPERATION_UPLOAD:
                    clients_threads(
                            exec_upload_saw, server, client_address,
                            client_packets_queue, packet,
                            file_storage, active_sessions, verbose)

                elif operation == OPERATION_DOWNLOAD:
                    clients_threads(
                            exec_download_saw, server, client_address,
                            client_packets_queue, packet,
                            file_storage, active_sessions, verbose)

            elif protocol == SR_PROTOCOL:
                if operation == OPERATION_UPLOAD:
                    clients_threads(
                            exec_upload_sr, server, client_address,
                            client_packets_queue, packet,
                            file_storage, active_sessions, verbose)

                elif operation == OPERATION_DOWNLOAD:
                    clients_threads(
                            exec_download_sr, server, client_address,
                            client_packets_queue, packet,
                            file_storage, active_sessions, verbose)


main()

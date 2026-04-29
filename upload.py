import time
from lib.args_parser import parse_upload
from lib.relay import extend_wait
from lib.constants import LENGTH_PACKET, END_FLAG, OPERATION_UPLOAD, \
                          SAW_PROTOCOL, SR_PROTOCOL, WINDOW_SIZE, \
                          MAX_SEQ, TIMEOUT
from lib.selective_repeat import load_data_in_buffer_sr, \
                                 send_packet_to_receiver_sr, \
                                 relay_no_ack_packet_to_receiver_sr
from lib.stop_and_wait import assemble_packet
import socket
import os
import select


# TODO pasar la lista a un dicc para optimizar recursos
# TODO doble espera en el SAW, debido a los dos extend_wait
# TODO optimizar select.select

'''
- Optimizar el UPLOAD SAW SR.
- Modificar Header -> Modificar los .lua
- Arreglar los timeout del SAW y del SR en el DOWNLOAD.
- Optimzar el DOWNLOAD
- Caso de error.
- Flujo de erroes, capa de aplicación.
'''

# COMANDO (NO BORRAR):
# python3 upload.py -H 127.0.0.1 -p 8080 -s archivo.txt -n
# copia.txt -r stop_and_wait -v


def selective_repeat_upload(operation, seq, end, ip, port,
                            file_path, file_name, protocol, verbose, client):
    buffer_data = {}
    send_base = 0
    next_seq_num = 0
    no_ack_packets = {}
    server_address = (ip, port)

    header_size = len((f"{protocol}|{operation}|{file_name}|"
                       f"{seq:02d}|{end}|").encode('utf-8'))

    load_data_in_buffer_sr(file_path, header_size, buffer_data)

    length_data = len(buffer_data)

    client.setblocking(False)

    while send_base < length_data:
        while (
            next_seq_num < send_base + WINDOW_SIZE
            and next_seq_num < length_data
        ):
            send_packet_to_receiver_sr(client, server_address, protocol,
                                       operation, file_name, next_seq_num,
                                       verbose, buffer_data, no_ack_packets,
                                       length_data)
            next_seq_num += 1
        ready, _, _ = select.select([client], [], [], 0.03)
        if ready:
            try:
                while True:
                    ack_packet, _ = client.recvfrom(LENGTH_PACKET)

                    ack_seq = int(ack_packet.decode('utf-8'))

                # eiliminamos clave-valor de diccionario que ya recibió el ack.
                    distancia = (ack_seq - (send_base % MAX_SEQ) + MAX_SEQ) % MAX_SEQ
                    seq_absoluto = send_base + distancia

                    if ack_seq in no_ack_packets:
                        del no_ack_packets[ack_seq]
                        if seq_absoluto in buffer_data:
                            del buffer_data[seq_absoluto]

                    while (
                        (send_base % MAX_SEQ) not in no_ack_packets
                        and send_base < next_seq_num
                    ):
                        send_base += 1

                    # tan rapido se libere espacio en la ventana, enviar nuevos paquetes
                    while (
                        next_seq_num < send_base + WINDOW_SIZE
                        and next_seq_num < length_data
                    ):
                        send_packet_to_receiver_sr(client, server_address, protocol,
                                                   operation, file_name, next_seq_num,
                                                   verbose, buffer_data, no_ack_packets,
                                                   length_data)
                        next_seq_num += 1
            except BlockingIOError:
                pass
            except Exception:
                pass

        relay_no_ack_packet_to_receiver_sr(client, server_address, protocol,
                                           operation, file_name, verbose,
                                           buffer_data, no_ack_packets,
                                           length_data)

    client.close()
    print("[SR] File upload successfully!")


'''------------------------------------------------------------------------'''


def send_file_data_to_server(client, ip, port, protocol, file_path,
                             operation, file_name, seq, end, verbose):
    with open(file_path, 'rb') as file:
        while True:
            packet, result = assemble_packet(file, protocol, operation,
                                             file_name, seq)

            if not result:
                break

            if extend_wait(client, packet, ip, port, verbose, seq, end):
                seq = 1 - seq
            else:
                break

    file.close()

    end = END_FLAG

    last_message = (f"{protocol}|{operation}|{file_name}|{seq}|"
                    f"{end}|").encode('utf-8')
    extend_wait(client, last_message, ip, port, verbose, seq, end)

    if verbose == 1:
        print("[FINISH] end_flag detected")


def stop_and_wait_upload(operation, seq, end, ip,
                         port, file_path, file_name,
                         protocol, verbose, client):

    data = ""

    message = (f"{protocol}|{operation}|"
               f"{file_name}|{seq}|{end}|").encode('utf-8')
    message = message + data.encode('utf-8')
    if not extend_wait(client, message, ip, port, verbose, seq, end):
        print("ERROR: Connection lost with the server")
        return

    seq = 1 - seq

    send_file_data_to_server(client, ip, port, protocol,
                             file_path, operation, file_name,
                             seq, end, verbose)

    print("[SAW] File upload successfully!")
    client.close()


def main():
    start_time = time.perf_counter()
    tokens = parse_upload()
    operation = OPERATION_UPLOAD
    seq = 0
    end = 0
    ip = tokens[0]
    port = tokens[1]
    file_path = tokens[2]
    file_name = tokens[3]
    protocol = tokens[4]
    verbose = 1 if tokens[5] is True else 0
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if not os.path.exists(file_path):
        print(f"[ERROR] The file was not found in: {file_path}")
        return

    if tokens[4] == SAW_PROTOCOL:
        stop_and_wait_upload(operation, seq, end, ip,
                             port, file_path, file_name,
                             protocol, verbose, client)
    elif tokens[4] == SR_PROTOCOL:
        selective_repeat_upload(operation, seq, end, ip,
                                port, file_path, file_name,
                                protocol, verbose, client)
        end_time = time.perf_counter()
        duration = end_time - start_time
        minutos, segundos = divmod(duration, 60)
        print(f"Tiempo total: {int(minutos):02d}:{int(segundos):02d}")
        print(f"Transferencia completada en: {duration:.4f} segundos")


main()

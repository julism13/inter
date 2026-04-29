from lib.constants import LENGTH_PACKET, \
                          MAX_SEQ, TIMEOUT, WINDOW_SIZE, END_FLAG
import time


def load_data_in_buffer_sr(file_path, header_size, data_buffer):
    with open(file_path, 'rb') as file:
        while True:
            available_space = LENGTH_PACKET - header_size
            data = file.read(available_space)
            if not data:
                break
            data_buffer.append(data)
    file.close()


def send_packet_to_receiver_sr(transmitter, receiver_address,
                               protocol, operation, file_name,
                               seq_abs_transmitter, verbose,
                               data_buffer_transmitter,
                               no_ack_packets_transmitter):
    end_flag_transmitter = (
        1 if seq_abs_transmitter == len(data_buffer_transmitter) - 1 else 0)
    ring_seq = seq_abs_transmitter % MAX_SEQ

    if verbose == 1:
        print(f"[SEND] packet: {ring_seq} | seq_abs: "
              f"{seq_abs_transmitter} | end_flag: {end_flag_transmitter}")

    if end_flag_transmitter == 1 and verbose == 1:
        print("[FINISH] end_flag detected")

    header = (f"{protocol}|{operation}|{file_name}|{ring_seq:02d}"
              f"|{end_flag_transmitter}|").encode('utf-8')
    packet = header + data_buffer_transmitter[seq_abs_transmitter]

    transmitter.sendto(packet, receiver_address)
    no_ack_packets_transmitter[ring_seq] = {'time': time.time(),
                                            'abs_seq': seq_abs_transmitter}


def relay_no_ack_packet_to_receiver_sr(transmitter, receiver_address,
                                       protocol, operation, file_name,
                                       verbose, data_buffer_transmitter,
                                       no_ack_packets_transmitter):
    current_time = time.time()

    for ring_seq, packet_info in list(no_ack_packets_transmitter.items()):
        if current_time - packet_info['time'] > TIMEOUT:
            send_packet_to_receiver_sr(transmitter, receiver_address,
                                       protocol, operation, file_name,
                                       packet_info['abs_seq'], verbose,
                                       data_buffer_transmitter,
                                       no_ack_packets_transmitter)


def receiver_received_future_packet(ring_seq, expected_ring_seq):
    distance = (ring_seq - expected_ring_seq) % MAX_SEQ
    return 0 < distance < WINDOW_SIZE


def manage_receiver_window_sr(packet, transmitter, receiver_address,
                              expected_seq, file,
                              data_buffer_transmitter, verbose):
    parts = packet.split(b'|', 5)
    seq = int(parts[3].decode())
    end = int(parts[4].decode())
    data = parts[5]

    if verbose == 1:
        print(f"[RECV] packet {seq} received."
              f" Expected: {expected_seq}")
        print(f"[ACK] sending ACK:{seq}")

    transmitter.sendto(str(seq).encode(), receiver_address)

    if seq == expected_seq:
        if verbose == 1:
            print(f"Packet {seq} is expected. Writing to file...")

        file.write(data)
        expected_seq = (expected_seq + 1) % MAX_SEQ
        upload_complete = (end == END_FLAG)

        while expected_seq in data_buffer_transmitter and not upload_complete:
            data_buff, end_buff = data_buffer_transmitter.pop(expected_seq)

            file.write(data_buff)

            if verbose == 1:
                print(f"[BUF] droped {expected_seq} from buffer "
                      f"and wrote to file.")

            expected_seq = (expected_seq + 1) % MAX_SEQ
            if end_buff == END_FLAG:
                upload_complete = True

        if upload_complete:
            return False, expected_seq

    elif receiver_received_future_packet(seq, expected_seq):
        if verbose == 1:
            print(f"[BUF] packet {seq} arrived out of order "
                  f"Storing in buffer.")
        data_buffer_transmitter[seq] = (data, end)

    return True, expected_seq

from lib.constants import LENGTH_PACKET


def assemble_packet(file, protocol, operation, file_name, seq):
    header = (f"{protocol}|{operation}|{file_name}|"
              f"{seq:02d}|0|").encode('utf-8')

    available_space = LENGTH_PACKET - len(header)
    data = file.read(available_space)

    if not data:
        return None, False

    packet = header + data

    return packet, True

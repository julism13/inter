import argparse

SERVER_SERVICE = 'server'
UPLOAD_SERVICE = 'upload'
DOWNLOAD_SERVICE = 'download'


def print_args(args, service):
    if not args.verbose:
        return

    print(f"\n--- DATOS CAPTURADOS ({service.upper()}) ---")
    print(f"IP del servidor: {args.host}")
    print(f"Puerto:          {args.port}")

    if service == UPLOAD_SERVICE:
        print(f"Archivo origen:  {args.src}")
        print(f"Nombre destino:  {args.name}")
        print(f"Protocolo:       {args.protocol}")
    elif service == DOWNLOAD_SERVICE:
        print(f"Archivo destino: {args.dst}")
        print(f"Nombre destino:  {args.name}")
        print(f"Protocolo:       {args.protocol}")
    elif service == SERVER_SERVICE:
        print(f"Ruta de Almacenamiento:  {args.storage}")

    print("----------------------------------------------\n")


def common_arguments(parser):
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-v', '--verbose',
                                 action='store_true',
                                 help='increase output verbosity')

    verbosity_group.add_argument('-q', '--quiet',
                                 action='store_true',
                                 help='decrease output verbosity')

    parser.add_argument('-H', '--host', metavar='ADDR',
                        help='server IP address', required=True)

    parser.add_argument('-p', '--port', type=int,
                        help='server port', required=True)


def parse_upload():
    parser = argparse.ArgumentParser(prog='upload',
                                     description='upload client')

    common_arguments(parser)

    parser.add_argument('-s', '--src', metavar='FILEPATH',
                        help='source file path', required=True)

    parser.add_argument('-n', '--name', metavar='FILENAME',
                        help='file name', required=True)

    parser.add_argument('-r', '--protocol',
                        help='error recovery protocol', required=True)

    args = parser.parse_args()
    print_args(args, UPLOAD_SERVICE)
    return [args.host, args.port, args.src, args.name,
            args.protocol, args.verbose]


def parse_download():
    parser = argparse.ArgumentParser(prog='download',
                                     description='download client')

    common_arguments(parser)

    parser.add_argument('-d', '--dst', metavar='FILEPATH',
                        help='destination file path', required=True)

    parser.add_argument('-n', '--name', metavar='FILENAME',
                        help='file name', required=True)

    parser.add_argument('-r', '--protocol',
                        help='error recovery protocol', required=True)

    args = parser.parse_args()
    print_args(args, DOWNLOAD_SERVICE)

    return [args.host, args.port, args.dst,
            args.name, args.protocol, args.verbose]


def parse_server():
    parser = argparse.ArgumentParser(prog='start-server', description='server')
    common_arguments(parser)

    parser.add_argument('-s', '--storage', metavar='DIRPATH',
                        help='storage dir path', required=True)

    args = parser.parse_args()
    print_args(args, SERVER_SERVICE)
    return [args.host, args.port, args.storage, args.verbose]

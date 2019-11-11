import toml

import uuid
import os

from database import Database
from io import BytesIO
from loguru import logger
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response, FileResponse
from pyramid.view import view_config
import pyramid.httpexceptions
from signal import signal, SIGINT
from sys import exit


CONFIG_FILE = 'config\\config.toml'
SERVER = None


def setup(config_file: str):
    logger.warning("Hephaestus v0.2 Starting")

    with open(CONFIG_FILE, 'r', encoding='UTF-8') as infile:
        try:
            config_settings = toml.load(infile)
        except toml.TomlDecodeError as error:
            logger.exception("Configuration file malformed or missing.", error)
            raise
        else:
            logger.info(f"Configuration: {CONFIG_FILE}")
            logger.info(f"Database: '{config_settings['database']['database']}'")

            if "key" in config_settings["upload"]:
                logger.info("Upload key in use.  Database is in RW mode.")
            else:
                logger.warning("Launched in Read-Only Mode.  No upload key present. "
                               "You will NOT BE ABLE TO POST IMAGES TO THE DATABASE.")

    if "file" in config_settings["log"]:
        logger.add(config_settings["log"]["file"], rotation='2mb')
        logger.info(f'Log File: {config_settings["log"]["file"]}')
    else:
        logger.warning("No Log file specified in configuration. Console Output only.")

    return config_settings


Settings = setup(CONFIG_FILE)


def convert_file_to_blob(data):
    binary_stream = BytesIO()
    binary_stream.write(data)
    return binary_stream.read()


def validate_token(token) -> bool:
    if "key" not in Settings['upload']:
        return False

    return True if token == Settings['upload']['key'] else False


def clear_temp():
    dir = '.\\temp'
    for file in os.listdir(dir):
        os.remove(dir + '\\' + file)


def sig_handler(signal_received, frame):
    logger.warning("SIGINT or CTRL-C detected.  Exiting.")
    exit(0)


@view_config(route_name='root')
def root_view(request):
    return FileResponse('static\\thehellisthis.gif')


@view_config(route_name='image')
def get_image(request):
    if 'uuid' not in request.matchdict:
        logger.info(f"Bad or malformed request from {request.client_addr}")
        raise pyramid.httpexceptions.HTTPBadRequest

    clear_temp()

    image_request = request.matchdict['uuid']

    query = db.query(image_request)
    if query is None:
        logger.info(f"Bad Request '{image_request}' from {request.client_addr}")
        raise pyramid.httpexceptions.HTTPNotFound
    else:
        logger.info(f"Serving Image '{image_request} to {request.client_addr}")
        db.add_view(image_request)
        temp_path = f'temp\\{uuid.uuid4()}.tmp'
        temp_file = open(temp_path, 'wb')
        temp_file.write(bytes(query[2]))
        response = FileResponse(temp_path, request=request, content_type='image/jpg')
        temp_file.close()
        return response


@view_config(route_name="upload", request_method='POST')
def send_image(request):
    # Validate authorization header
    if 'authorization' not in request.headers:
        logger.warning(f"Unauthorized upload attempt: {request.client_addr}")
        raise pyramid.httpexceptions.HTTPForbidden

    # check header:
    if not validate_token(request.headers['authorization']):
        logger.warning(f"Invalid upload token: {request.headers['authorization']} "
                       f"from {request.client_addr}")
        raise pyramid.httpexceptions.HTTPForbidden

    logger.info(f"POST from {request.client_addr}")
    post_data = request.POST

    with request.POST['item'].file as input_file:
        new_blob = BytesIO()
        new_blob.write(input_file.read())

    new_uuid = uuid.uuid4()
    db.insert(new_uuid, new_blob)

    logger.info(f"New Database Entry: {new_uuid}")

    return Response(str(new_uuid))


if __name__ == "__main__":
    signal(SIGINT, sig_handler)
    clear_temp()
    db = Database()

    # Pyramid config
    with Configurator() as config:
        config.add_route('image', '/img/{uuid}')
        config.add_route('root', '/')
        # config.add_route('short_link', '/s/{link}') TODO: These are upcoming
        # config.add_route('short_link1', '/s')
        config.add_route('upload', '/upload')
        config.scan()
        app = config.make_wsgi_app()

    server = make_server(Settings['network']['ip'], Settings['network']['port'], app)

    while True:
        server.serve_forever()

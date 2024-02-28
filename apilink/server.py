import sys
import os
import signal
import argparse
import time
import re
from datetime import datetime as dt
from mimetypes import guess_type
from tornado.web import Application, RequestHandler, Finish, StaticFileHandler
from tornado.ioloop import IOLoop, PeriodicCallback
from base_logger import logger, set_logger_level
from vu_notifications import show_error_msg, show_info_msg
from vu_filesystem import VU_FileSystem
from link_manager import LinkManager

class BaseHandler(RequestHandler):
    def initialize(self, link_manager):
        self.link_manager = link_manager # pylint: disable=attribute-defined-outside-init
        self.upload_path = VU_FileSystem.get_upload_directory_path() # pylint: disable=attribute-defined-outside-init

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header('Access-Control-Allow-Methods', ' PUT, DELETE, OPTIONS, GET')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET')
        self.set_header('Content-Type', 'application/json')

        # self.set_header("Access-Control-Allow-Origin", "Origin");
        # self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization");
        # self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        # self.set_header("Access-Control-Allow-Credentials", "true");

    # Helper function to send response
    def send_response(self, status, message='', data=None, status_code=200):
        resp = {'status': status, 'message': message, 'data': data}
        self.set_status(status_code)
        self.write(resp)
        self.finish()

class Status_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        return self.send_response(status='ok', message='API Link Up and Running')

class Link_List_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        links = self.link_manager.get_active_links()
        return self.send_response(status='ok', data=links)

class Link_Reload_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        links = self.link_manager.reload_all_links()
        return self.send_response(status='ok', data=links)

class Link_Enable_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        link_file = self.get_argument('link', None)

        if link_file is None:
            logger.debug("Link file name is empty!")
            return self.send_response(status='fail', message='Invalid link file!')

        if self.link_manager.enable_link(link_file):
            logger.info(f"Link `{link_file}` is now enabled.")
            return self.send_response(status='ok')
        return self.send_response(status='fail', message='Failed to enable link')

class Link_Disable_Handler(BaseHandler):
    async def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        link_file = self.get_argument('link', None)

        if link_file is None:
            logger.debug("Link file name is empty!")
            return self.send_response(status='fail', message='Invalid link file!')

        res = await self.link_manager.disable_link(link_file)
        if res:
            logger.info(f"Link `{link_file}` is now disabled.")
            return self.send_response(status='ok')
        return self.send_response(status='fail', message='Failed to disable link')

class Link_Delete_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        link_file = self.get_argument('link', None)

        if link_file is None:
            return self.send_response(status='fail', message='Invalid link file!')

        if self.link_manager.delete_link(link_file):
            return self.send_response(status='ok')
        return self.send_response(status='fail', message='Failed to disable link')

class Link_Read_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        link_file = self.get_argument('link', None)
        requested_type = self.get_argument('type', None)

        if link_file is None:
            logger.debug("Link file name is empty!")
            return self.send_response(status='fail', message='Invalid link file!')

        raw = False
        if requested_type == 'toml':
            raw = True
            logger.debug("TOML is requested")

        link_contents = self.link_manager.get_link_contents(link_file, raw=raw)
        return self.send_response(status='ok', data={'contents': link_contents})

class Link_Write_Handler(BaseHandler):
    def post(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        link_filename = self.get_argument('link_filename', None)
        link_contents = self.get_argument('link_contents', None)

        if link_filename is None:
            return self.send_response(status='fail', message='Invalid link filename!')
        if link_contents is None:
            return self.send_response(status='fail', message='Invalid link contents!')

        if self.link_manager.create_link(link_filename, link_contents):
            return self.send_response(status='ok')
        return self.send_response(status='fail', message='Failed to create link')

class Link_Update_Handler(BaseHandler):
    def post(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        link_filename = self.get_argument('link_filename', None)
        link_contents = self.get_argument('link_contents', None)

        if link_filename is None:
            logger.debug("Invalid link filename.")
            return self.send_response(status='fail', message='Invalid link filename!')

        if link_contents is None:
            logger.debug("Invalid link content.")
            return self.send_response(status='fail', message='Invalid link contents!')

        if self.link_manager.update_link(link_filename, link_contents):
            return self.send_response(status='ok')
        return self.send_response(status='fail', message='Failed to create link')

class Time_Unix_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        data = { 'unixtime': time.time() }
        return self.send_response(status='ok', data=data)

class Time_DateTime_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        date_format = self.get_argument('format', '%H:%M:%S %d-%m-%Y')
        now = dt.now()

        data = { 'datetime': now.strftime(date_format) }
        return self.send_response(status='ok', data=data)

class Server_Reload_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)
        return self.send_response(status='ok')

class Link_Get_Image_Handler(BaseHandler):
    def get(self):
        image = self.get_argument('file', 'img_blank')

        logger.debug(f"Request:{self.__class__.__name__}: {image}")
        self.set_header("Content-Type", "image/png")
        image_path = os.path.join(VU_FileSystem.get_link_images_folder_path(), image)

        if os.path.isfile(image_path):
            filepath = image_path
            logger.debug(f"Serving image from {filepath}")
        else:
            filepath = os.path.join(VU_FileSystem.get_link_images_folder_path(), 'blank.png')
            logger.debug(f"Serving DEFAULT image from {filepath}")

        try:
            with open(filepath, 'rb') as f:
                data = f.read()
                self.write(data)
            return self.finish()
        except IOError as e:
            logger.error(e)
            return self.send_response(status='fail', message='Internal sever error!', status_code=500)

class Link_Image_List_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        images = VU_FileSystem.get_image_list()
        return self.send_response(status='ok', data={'images': images})

class Link_Image_Delete_Handler(BaseHandler):
    def get(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        image = self.get_argument('file', None)

        if image is None:
            return self.send_response(status='fail', message='Invalid image name!')

        image_path = os.path.join(VU_FileSystem.get_link_images_folder_path(), image)

        if os.path.isfile(image_path):
            os.remove(image_path)
            logger.debug(f"Deleting image `{image_path}`")
            return self.send_response(status='ok', message='Image removed')

        return self.send_response(status='fail', message='File does not exist!')

class Link_Image_Upload_Handler(BaseHandler):
    def post(self):
        logger.debug(f"Request:{self.__class__.__name__}")
        image_name = self.get_argument('image_name', None)
        image_data = self.request.files.get('image_file', None)
        image_filename = image_data[0].get('filename', None)

        if image_name is None:
            logger.debug(f"Invalid image name. {image_name}")
            return self.send_response(status='fail', message='Image name missing!')

        if image_data is None or not image_filename.endswith('.png'):
            logger.debug(f"Invalid image file. (`{image_data}`)")
            return self.send_response(status='fail', message='Image file missing!')

        if len(image_name) < 3:
            logger.debug(f"Image name too short! `{image_name}`")
            return self.send_response(status='fail', message='Image name too short!')

        # Check file name
        if not re.match(r"^[0-9a-z\-\_\ ]*?$", image_name, re.IGNORECASE):
            logger.error(f"Invalid name for image! ({image_name})")
            return self.send_response(status='fail', message=f'Invalid name for image! ({image_name})')

        # Check content type
        allowed_content_type = ['image/png']
        content_type = image_data[0].get('content_type', None)
        if content_type not in allowed_content_type:
            logger.error(f"Invalid image file! ({image_name})")
            return self.send_response(status='fail', message=f'Invalid content type! ({content_type})')

        # Handle image upload
        file_path = os.path.join(VU_FileSystem.get_link_images_folder_path(), f"{image_name}.png")
        with open(file_path, 'wb') as img:
            img.write(image_data[0]['body'])

        logger.debug(f"Image uploaded to `{file_path}`.")
        return self.send_response(status='ok')


# -- Default 404 --
class Default_404_Handler(RequestHandler):
    # Override prepare() instead of get() to cover all possible HTTP methods.
    def prepare(self):
        self.set_status(404)
        resp = {'status': 'fail', 'message': 'Unsupported method'}
        self.write(resp)
        raise Finish()

class FileHandler(RequestHandler):
    def get(self, path=None):
        if path:
            logger.debug(f"Requesting: {path}")
            file_location = os.path.join(VU_FileSystem.get_www_folder_path(), path)
        else:
            file_location = os.path.join(VU_FileSystem.get_www_folder_path(), 'index.html')

        if not os.path.isfile(file_location):
            logger.error(f"Requested file can not be found: {path}")
            self.set_status(404)
            resp = {'status': 'fail', 'message': 'Page not found'}
            self.write(resp)
            raise Finish()
        content_type, _ = guess_type(file_location)
        self.add_header('Content-Type', content_type)
        with open(file_location, encoding="utf-8") as source_file:
            self.write(source_file.read())


class VU_API_Link(Application):
    def __init__(self):
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        logger.info("Loading server config...")
        self.config = None
        self.link_manager = LinkManager()

        shared_resources = { "link_manager":self.link_manager }

        self.handlers = [
            ("/api/v0/link/list", Link_List_Handler, shared_resources),
            ("/api/v0/link/reload", Link_Reload_Handler, shared_resources),
            ("/api/v0/link/enable", Link_Enable_Handler, shared_resources),
            ("/api/v0/link/disable", Link_Disable_Handler, shared_resources),
            ("/api/v0/link/read", Link_Read_Handler, shared_resources),
            ("/api/v0/link/write", Link_Write_Handler, shared_resources),
            ("/api/v0/link/update", Link_Update_Handler, shared_resources),
            ("/api/v0/link/delete", Link_Delete_Handler, shared_resources),
            ("/api/v0/image/get", Link_Get_Image_Handler, shared_resources),
            ("/api/v0/image/list", Link_Image_List_Handler, shared_resources),
            ("/api/v0/image/upload", Link_Image_Upload_Handler, shared_resources),
            ("/api/v0/image/delete", Link_Image_Delete_Handler, shared_resources),
            ("/api/v0/time/unix", Time_Unix_Handler, shared_resources),
            ("/api/v0/time/datetime", Time_DateTime_Handler, shared_resources),
            ("/api/v0/server/status", Status_Handler, shared_resources),
            ("/api/v0/server/reload", Server_Reload_Handler, shared_resources),

            ("/", FileHandler),
            (r'/(.*)', StaticFileHandler, {'path': VU_FileSystem.get_www_folder_path()}),
        ]

        self.server_settings = {
            "debug": True,
            "autoreload": False,
            # "autoreload": True,
            "default_handler_class": Default_404_Handler,
        }

    def signal_handler(self, signal, frame):
        IOLoop.current().add_callback_from_signal(self.shutdown_server)
        print('\r\nYou pressed Ctrl+C!')
        show_info_msg("CTRL+C", "CTRL+C pressed.\r\nVU API Link app will exit now.")  # Remove if becomes annoying
        sys.exit(0)

    def shutdown_server(self):
        logger.info('Stopping API server')
        logger.info('Will shutdown in 3 seconds ...')
        io_loop = IOLoop.instance()
        deadline = time.time() + 3

        def stop_loop():
            now = time.time()
            if now < deadline and (io_loop._callbacks or io_loop._timeouts):
                io_loop.add_timeout(now + 1, stop_loop)
            else:
                io_loop.stop()
                logger.info('Shutdown')
        stop_loop()

    def run_forever(self):
        logger.info("Karanovic Research Dials - Starting API Link server")
        app = Application(self.handlers, **self.server_settings)

        # server_config = self.config.get_server_config()
        # port = server_config.get('port', 5340)
        # dial_update_period = server_config.get('dial_update_period', 1000)
        port = 5341
        scheduler_period = 500
        logger.info(f"VU1 API LINK is listening on http://localhost:{port}")

        pc = PeriodicCallback(self.link_manager.async_periodic_update, scheduler_period)
        pc.start()

        app.listen(port)
        IOLoop.instance().start()

def main(cmd_args=None):
    if cmd_args is None:
        set_logger_level('info')
    else:
        set_logger_level(cmd_args.logging)
    try:
        VU_API_Link().run_forever()
    except Exception:
        logger.exception("VU API Link service crashed during setup.")
        show_error_msg("Crashed", "VU API Link has crashed unexpectedly!\r\nPlease check log files for more information.")
        sys.exit(-1)
    sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Karanovic Research - VU API Link')
    parser.add_argument('-l', '--logging', type=str, default='debug', help='Set logging level. Default is `info`')
    args = parser.parse_args()
    main(args)

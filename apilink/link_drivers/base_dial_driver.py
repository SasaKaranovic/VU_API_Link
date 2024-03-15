import os
import requests
from tornado.httpclient import AsyncHTTPClient
from apilink.base_logger import logger
from apilink.vu_filesystem import VU_FileSystem

class DialDriver:
    def __init__(self, vu_dial_uid, vu_api_key, vu_host='localhost', vu_port=5340):
        # pylint: disable=too-many-instance-attributes
        self.http_client = AsyncHTTPClient()
        self.vu_dial_uid = vu_dial_uid
        self.vu_api_key = vu_api_key
        self.vu_host = vu_host
        self.vu_port = vu_port
        self.current_percent = 0 # Last value sent to dial
        self.percent = 0 # Latest value
        self.image = 'img_blank.png'
        self.image_upload_pending = False
        self.backlight = { 'red': 0, 'green': 0, 'blue': 0 }
        self.backlight_map = None

    def _make_url(self, handler, keyVal=None):
        url_parameters = ""
        if keyVal is not None:
            url_parameters = '&' + '&'.join(f'{str(key)}={str(val)}' for key, val in keyVal.items())
        return f"http://{self.vu_host}:{self.vu_port}/api/v0/dial/{self.vu_dial_uid}/{handler}?key={self.vu_api_key}{url_parameters}"

    async def _update_value(self):
        response = await self.http_client.fetch(self._make_url('set', {'value': self.percent}), method='GET', request_timeout=10)
        if response.code == 200:
            self.current_percent = self.percent
            logger.debug(f"Dial `{self.vu_dial_uid}` updated to {self.percent}%")
            return True

        logger.error(f"Failed to update dial `{self.vu_dial_uid}`. Server status code {response.code}")
        return False

    async def _update_backlight(self):
        response = await self.http_client.fetch(
                                                self._make_url('backlight',
                                                {
                                                    'red': self.backlight['red'],
                                                    'green': self.backlight['green'],
                                                    'blue': self.backlight['blue']
                                                }),
                                                method='GET', request_timeout=10)
        if response.code  == 201:
            logger.debug(f"Dial `{self.vu_dial_uid}` backlight updated to R:{self.backlight['red']} G:{self.backlight['green']} B:{self.backlight['blue']}")
            return True
        if response.code  == 200:
            logger.debug(f"Dial `{self.vu_dial_uid}` backlight is already at R:{self.backlight['red']} G:{self.backlight['green']} B:{self.backlight['blue']}")
            return True
        logger.error(f"Failed to update dial `{self.vu_dial_uid}` backlight. Server status code {response.code}")
        return False

    def _update_image(self):
        if not self.image_upload_pending:
            return True

        img_file = os.path.join(VU_FileSystem.get_link_images_folder_path(), self.image)

        if not os.path.isfile(img_file):
            logger.error(f"Image `{img_file}` does not exist! Aborting.")
            self.image_upload_pending = False
            return False

        files = {'imgfile': open(img_file, 'rb'), 'key': self.vu_api_key}
        response = requests.post(self._make_url('image/set'), files=files, timeout=10)

        if response.status_code == 201:
            self.image_upload_pending = False
            logger.debug(f"Dial `{self.vu_dial_uid}` image updated")
            return True
        if response.status_code == 200:
            logger.debug(f"Dial `{self.vu_dial_uid}` is already at the correct image.")
            return True

        logger.error(f"Failed to update dial `{self.vu_dial_uid}` image. Server status code {response.status_code}")
        return False

    def _recalculate_backlight(self):
        if self.backlight_map is None:
            return False

        # Then as we cross threshold, use that color
        for value, rgb in self.backlight_map.items():
            if self.percent >= int(value):
                self.backlight['red'] = int(rgb[0])
                self.backlight['green'] = int(rgb[1])
                self.backlight['blue'] = int(rgb[2])
        return True

    def set_dial_value(self, percent):
        self.percent = int(percent)

    def set_dial_image(self, image):
        self.image = image
        self.image_upload_pending = True

    def set_backlight_map(self, colormap):
        self.backlight_map = colormap

    async def update(self):
        # Is update necessary?
        if self.percent == self.current_percent:
            return

        try:
            # Update value
            response = await self._update_value()
            if not response:
                logger.error("Failed to update dial value!")
                return response

            # Update backlight
            if self._recalculate_backlight():
                response = await self._update_backlight()
                if not response:
                    logger.error("Failed to update dial backlight!")
                    return response

            # Update image
            response = self._update_image()
            if not response:
                logger.error("Failed to update dial image!")
                return response

            return response
        except Exception as e:
            logger.error(e)
            return False

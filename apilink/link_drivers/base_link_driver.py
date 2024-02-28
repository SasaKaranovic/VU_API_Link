import os
import time
from tomlkit import dumps
from tomlkit import parse
from apilink.base_logger import logger
from apilink.vu_filesystem import VU_FileSystem
from apilink.link_drivers.base_dial_driver import DialDriver
from apilink.link_drivers.value_modifiers import ValueModifiers


class BaseLinkDriver:
    def __init__(self, cfg_file):
        # pylint: disable=too-many-instance-attributes
        self.ready = False
        self.dial_value = 0
        self.api_value = 0
        self.next_update = 0
        self.retry_delay = 60
        self.mod = ValueModifiers()

        self.cfg = { 'info':{}, 'api':{} }
        self.cfg['info']['file'] = cfg_file
        self.cfg['info']['image'] = None
        self.cfg['info']['description'] = 'No Description'
        self.cfg['info']['enabled'] = True
        self.cfg['api']['value_modifiers'] = []

        self.cfg_file = cfg_file

        if not self._load_config():
            return

        self.dial_driver = DialDriver( vu_dial_uid=self.cfg['dial']['uid'],
                                       vu_api_key=self.cfg['dial']['api_key'],
                                       vu_host=self.cfg['dial']['host'],
                                       vu_port=self.cfg['dial']['port'] )

        self.available_modifiers = [func for func in dir(self.mod) if callable(getattr(ValueModifiers, func)) and not func.startswith("__")]

        if self.cfg['info']['image'] is not None:
            self.set_dial_image(self.cfg['info']['image'])

        if self.cfg.get('backlight_map', None) is not None:
            logger.debug(f"Applying backlight map: {self.cfg['backlight_map']}")
            self.dial_driver.set_backlight_map(self.cfg['backlight_map'])

        self.ready = True

    def _check_keys_exist(self, required, check_list):
        if set(required).issubset(check_list):
            return True
        return False

    def _load_config(self):
        filepath = os.path.join(VU_FileSystem.get_links_folder_path(), self.cfg_file)
        if not os.path.exists(filepath):
            logger.error(f"Can not load link '{self.cfg_file}'. Config file '{filepath}' does not exist!")
            return None

        with open(filepath, 'r', encoding="utf-8") as file:
            cfg = file.read()  # pylint: disable=assignment-from-no-return


        if cfg is None:
            logger.error(f"Link file for '{self.cfg_file}' is empty or corrupt.")
            return None

        # Parse TOML file
        cfg = parse(cfg)

        # Define required keys every config must have
        required_keys = {
            'info':  ['name', 'description'],
            'api':  ['url', 'item', 'update_period'],
            'dial':  ['uid', 'host', 'port', 'api_key'],
        }

        logger.debug(cfg)

        # Check top-level keys
        if not self._check_keys_exist(required_keys.keys(), cfg):
            logger.error(f"Link file '{self.cfg_file}' must contain {required_keys.keys()} keys!")
            logger.error("This link will be ignored")
            return None

        for key, value in required_keys.items():
            if not self._check_keys_exist(value, cfg[key]):
                logger.error(f"Link file '{key}' section must contain `{value}` keys!")
                logger.error("This link will be ignored")
                return None

        # Update class cfg
        self.cfg = cfg

        return True

    def save_config(self):
        filepath = os.path.join(VU_FileSystem.get_links_folder_path(), self.cfg_file)

        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(dumps(self.cfg))
        return True

    def get_config(self, raw=False):
        if raw:
            return dumps(self.cfg)
        return self.cfg

    def get_headers(self):
        return self.cfg['api'].get('headers', None)

    def is_ready(self):
        return self.ready

    def set_next_update(self, value):
        self.next_update = value
        return True

    def get_next_update(self):
        return self.next_update

    def is_enabled(self):
        return self.cfg['info']['enabled']

    def enable(self):
        self.cfg['info']['enabled'] = True
        self.save_config()
        self.next_update = time.time()
        return True

    async def disable(self):
        self.cfg['info']['enabled'] = False
        self.save_config()
        self.set_dial_value(0)
        await self.dial_driver.update()
        return True

    def soft_disable(self):
        self.cfg['info']['enabled'] = False

    def get_driver(self):
        return self.cfg['info']['driver']

    def get_name(self):
        return self.cfg['info']['name']

    def get_dial_uid(self):
        return self.cfg['dial']['uid']

    def fetch(self):
        raise NotImplementedError

    async def update(self):
        raise NotImplementedError

    def set_dial_value(self, dial_value):
        self.dial_driver.set_dial_value(dial_value)

    def set_dial_image(self, image):
        self.dial_driver.set_dial_image(image)


    def apply_modifiers(self):
        mod_list = self.cfg['api'].get('value_modifiers', [])
        if len(mod_list) <= 0:
            return

        for modifier in mod_list:
            function_name = modifier.get('function', None)

            if str(function_name) not in self.available_modifiers:
                logger.error(f"Requested modifier {function_name} does not exist.")
                break

            # Call modifier function
            logger.debug(f"Applying modifier function `{function_name}`")
            func = getattr(self.mod, function_name)
            self.api_value = func( value=self.api_value, args=modifier )

        # Always apply sanity check
        logger.debug("Applying modifier function `value_clip`")
        self.api_value = self.mod.value_clip(value=self.api_value, args={})

import os
import re
from apilink.vu_filesystem import VU_FileSystem
from apilink.base_logger import logger
from apilink.link_drivers.driver_requests import Driver_Requests


class LinkManager:
    links = {}

    def __init__(self):
        self.links_path =  VU_FileSystem.get_links_folder_path()
        logger.info(f"Loading API Llinks from {self.links_path}")
        self._load_available_links()

    def _load_available_links(self):
        config_files = os.listdir(self.links_path)
        config_files = [item for item in config_files if item.endswith('.toml')]

        for cfg in config_files:
            if re.match(r"^[0-9a-z\-_\.]*?\.toml$", cfg, re.IGNORECASE):
                self._load_link(cfg)
            else:
                logger.error(f"Found .toml link file with invalid name (`{cfg}`)")


    def _load_link(self, link_file):
        logger.debug(f"Setting up link for {link_file}")

        if link_file.startswith('requests'):
            link_driver = Driver_Requests(link_file)

            if link_driver.is_ready():
                self._disable_if_dial_in_use(link_driver)
                self.links[link_file] = link_driver
                logger.info(f"Created '{link_driver.get_name()}' using 'requests' driver")
                return

            logger.info("Attempted to create 'link_driver.get_name()' using 'requests' but driver failed to start!")
            return

        # Catch-all
        logger.error(f"Config '{link_file}' has no driver.'")

    def _disable_if_dial_in_use(self, driver):
        return
        # uid = driver.get_dial_uid()

        # for _, val in self.links.items():
        #     if val.is_enabled():
        #         if uid == val.get_dial_uid():
        #             logger.error(f"Dial `{uid}` is already being used! Disabling to prevent collision.")
        #             driver.soft_disable()
        #             return

    def _unload_link(self, filename):
        # Remove link from loaded links
        res = self.links.pop(filename, None)
        if res is None:
            logger.error(f"Requested link `{filename}` does not exist.")
        else:
            logger.info(f"Requested link `{filename}` unloaded.")


    def _link_exists(self, link_file):
        if self.links.get(link_file, None) is None:
            return False
        return True

    def reload_all_links(self):
        backup_links = self.links
        self.links.clear()
        self._load_available_links()

        # Restore next update
        for key, driver in self.links.items():
            previous = backup_links.get(key, None)
            if previous is not None:
                driver.set_next_update(previous.get_next_update())

    def get_link_contents(self, link_file, raw=False):
        if not self._link_exists(link_file):
            logger.error(f"Link `{link_file}` does not exist!")
            return False

        return self.links[link_file].get_config(raw=raw)

    def enable_link(self, link_file):
        if not self._link_exists(link_file):
            logger.error(f"Link `{link_file}` does not exist!")
            return False

        logger.info(f"Link `{link_file}` enabled.")
        return self.links[link_file].enable()

    async def disable_link(self, link_file):
        if not self._link_exists(link_file):
            logger.error(f"Link `{link_file}` does not exist!")
            return False

        logger.info(f"Link `{link_file}` disabled.")
        return await self.links[link_file].disable()

    def delete_link(self, link_file):
        if not self._link_exists(link_file):
            logger.error(f"Link `{link_file}` does not exist!")
            return False

        if not link_file.endswith('.toml'):
            logger.error(f"Link `{link_file}` is not a toml file!")
            return False

        # Remove link from loaded links
        self._unload_link(link_file)

        # Remove link file
        rem_filepath = os.path.join(self.links_path, link_file)
        if os.path.isfile(rem_filepath):
            os.remove(rem_filepath)
            logger.info(f"Removed link file `{rem_filepath}`")
            return True

        logger.error(f"Failed to remove file `{rem_filepath}`")
        return False

    def create_link(self, filename, content):
        filename = filename.replace('.toml', '')
        filename = f'{filename}.toml'

        if self._link_exists(f'{filename}.toml'):
            logger.error(f"Link `{filename}.toml` already exists!")
            return False

        # Test file_name
        if not re.match(r"^[0-9a-z\-\_\.\ ]*?$", filename, re.IGNORECASE):
            logger.error(f"Invalid file name! ({filename})")
            return False

        # Prepare file name
        filename = filename.replace(' ', '_')   # Replace space with underscore
        filename = filename.replace('__', '_')  # Replace double_underscore
        filename = filename.replace('--', '-')  # Replace double-dash
        filename = f'requests_{filename.lower()}.toml'


        # Write content to file
        with open( os.path.join(self.links_path, filename), 'w', encoding='utf-8') as file:
            file.write(content)

        # Load new link
        self._load_link(filename)
        return True

    def update_link(self, filename, content):
        filename = filename.replace('.toml', '')
        filename = f'{filename}.toml'
        if not self._link_exists(filename):
            logger.error(f"Link `{filename}` does not exist!")
            return False

        # Unload the link file
        self._unload_link(filename)

        # Write content to file
        with open( os.path.join(self.links_path, filename), 'w', encoding='utf-8') as file:
            file.write(content)

        # Load new link
        self._load_link(filename)
        return True


    def get_active_links(self):
        configs = []
        for _, driver in self.links.items():
            configs.append(driver.get_config())
        return configs

    async def async_periodic_update(self) -> None:
        for _, link_driver in self.links.items():
            if link_driver.is_enabled():
                await link_driver.update()

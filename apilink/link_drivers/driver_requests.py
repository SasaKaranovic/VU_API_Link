import time
import json
from tornado.httpclient import AsyncHTTPClient
from apilink.link_drivers.base_link_driver import BaseLinkDriver
from apilink.base_logger import logger

class Driver_Requests(BaseLinkDriver):
    def __init__(self, cfg_file):
        super().__init__(cfg_file)
        self.cfg['info']['driver'] = 'requests'
        self.http_client = AsyncHTTPClient()

    async def update(self) -> None:
        if time.time() >= self.next_update:
            logger.debug(f"Fetching '{self.cfg['api']['url']}'")

            headers = self.get_headers()

            client = await self.http_client.fetch(request=self.cfg['api']['url'], headers=headers)
            response = json.loads(client.body.decode(errors="ignore"))

            try:
                self.api_value = eval(self.cfg['api']['item'])
                logger.debug(f"API response: '{response}'")
                logger.debug(f"Found target item `{self.cfg['api']['item']}`. Value: {self.api_value}")
            except KeyError:
                logger.error("API request did not contain item specified in the config!")
                logger.error(f"API:'{self.cfg['api']['url']}' Item:'{self.cfg['api']['item']}')")
                return False

            # 2. Update value
            logger.debug(f"API value: {self.api_value}")
            self.set_dial_value(self.api_value)

            # 3. Run modifiers (if required)
            self.apply_modifiers()

            # 4. Update dial value
            self.set_dial_value(self.api_value)

            # 5. Propagate changes by calling .update() on dial driver
            logger.debug(f"Final value: {self.api_value}")
            await self.dial_driver.update()

            # Mark that we actually updated the API call
            self.next_update = time.time() + int(self.cfg['api']['update_period'])

            # Update any new/values that have been added to the config to survive restart
            self.save_config()
            return True

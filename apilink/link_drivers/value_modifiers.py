import time
import random
from datetime import datetime as dt
from apilink.base_logger import logger

class ValueModifiers:
    def __init__(self):
        pass

    def _util_convert_seconds(self, value, unit):
        div = { 'seconds': 1, 'minutes': 60, 'hours': 3600, 'days': 86400 }

        if unit in div:
            result = round(value/div[unit], 1)
            logger.debug(f"_util_convert_seconds: Scaling value `{value}` seconds to `{unit}` -> {result}")
            return result

        logger(f"_util_convert_seconds: Invalid unit specified `{unit}`")
        return 0

    def value_clip(self, **kwargs):
        value = float(kwargs.get('value', 0.0))
        value_min = float(kwargs['args'].get('min', 0.0))
        value_max = float(kwargs['args'].get('max', 100.0))

        try:
            if int(value) >= value_max:
                return value_max
            if int(value) <= value_min:
                return value_min
            return int(value)
        except Exception as e:
            raise e

    def invert(self, **kwargs):
        value = float(kwargs.get('value', 0.0))
        return 100 - value

    def offset(self, **kwargs):
        value = float(kwargs.get('value', 0.0))
        offset_amount = float(kwargs['args'].get('amount', 0.0))
        return value + offset_amount

    def absolute(self, **kwargs):
        value = float(kwargs.get('value', 0.0))
        logger.debug(f"Returning absolute value of {value} as {abs(value)}")
        return abs(value)

    def scale_number(self, **kwargs):
        value = float(kwargs.get('value', 0.0))
        scale_min = float(kwargs['args'].get('min', 0.0))
        scale_max = float(kwargs['args'].get('max', 100.0))

        ret_value = (value-scale_min) / (scale_max - scale_min) * 100
        if value > scale_max:
            ret_value = scale_max
        elif value < scale_min:
            ret_value = scale_min

        logger.debug(f"Initial value was: {value} scaled to: {ret_value} (using min:{scale_min} max:{scale_max})")
        return ret_value

    def unix_time_delta(self, **kwargs):
        value = kwargs.get('value', 0)
        compare_to = kwargs['args'].get('compare_to', time.time())
        calculate = kwargs['args'].get('calculate', 'until')
        unit = kwargs['args'].get('unit', 'hours')
        ret_value = 0

        if compare_to == 'now':
            compare_to = time.time()

        if calculate == 'until':
            ret_value = compare_to - value
        else:
            ret_value = value - compare_to

        logger.debug(f"Value before conversion {ret_value}")
        return self._util_convert_seconds(ret_value, unit)


    def str_datetime_delta(self, **kwargs):
        value = kwargs.get('value', 0)
        date_format = kwargs['args'].get('date_format', '%d.%m.%y')
        compare_to = kwargs['args'].get('compare_to', 'Now')
        calculate = kwargs['args'].get('calculate', 'until')
        unit = kwargs['args'].get('unit', 'hours')

        try:

            if compare_to == 'now':
                now = dt.now()
                compare_to = now.strftime(date_format)
            else:
                compare_to = dt.strptime(compare_to, date_format)

            compare_date = dt.strptime(value, date_format)
            if calculate == 'until':
                delta = round((compare_to - compare_date).total_seconds(), 1)
            else:
                delta = round((compare_date - compare_to).total_seconds(), 1)

            logger.debug(f"Delta `{calculate}` between {compare_to} and {compare_date} is `{delta}` seconds.")

            return self._util_convert_seconds(delta, unit)

        except ValueError as e:
            logger.error(f"str_datetime_delta failure: {e}")

        return 0

    def random_value(self, **kwargs):
        start = kwargs['args'].get('min', 0)
        stop = kwargs['args'].get('max', 100)

        return random.randint(start, stop)

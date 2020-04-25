"""Gateway module connecting to Bosch thermostat."""

import logging
from .base_gateway import BaseGateway

from bosch_thermostat_client.connectors import NefitConnector
from bosch_thermostat_client.encryption import NefitEncryption as Encryption
from bosch_thermostat_client.const import XMPP, GATEWAY, MODELS, EMS, SYSTEM_BUS, VALUE, VALUES, REFERENCES, ID
from bosch_thermostat_client.const.nefit import NEFIT, PRODUCT_ID
from bosch_thermostat_client.exceptions import DeviceException


_LOGGER = logging.getLogger(__name__)


class NefitGateway(BaseGateway):
    """Gateway to Bosch thermostat."""

    device_type = NEFIT

    def __init__(self, session, session_type, host, access_key, password=None):
        """
        Initialize gateway.

        :param access_key:
        :param password:
        :param host:
        :param device_type -> IVT or NEFIT
        """
        if password:
            access_token = access_key.replace("-", "")
        self._connector = NefitConnector(
            host=host,
            loop=session,
            access_key=access_token,
            encryption=Encryption(access_token, password),
        )
        self._session_type = XMPP
        super().__init__(host)

    async def _update_info(self, initial_db):
        """Update gateway info from Bosch device."""
        for name, uri in initial_db.items():
            try:
                response = await self._connector.get(uri)
                if VALUE in response:
                    self._data[GATEWAY][name] = response[VALUE]
                elif name == SYSTEM_BUS:
                    self._data[GATEWAY][SYSTEM_BUS] = response.get(REFERENCES, [])
            except DeviceException as err:
                _LOGGER.debug("Can't fetch data for update_info %s", err)
                pass

    async def get_device_model(self, _db):
        """Find device model."""
        product_id = self._data[GATEWAY].get(PRODUCT_ID)
        model_scheme = _db[MODELS]
        for bus in self._data[GATEWAY].get(SYSTEM_BUS, []):
            if EMS in bus.get(ID, "").upper():
                self._bus_type = EMS
                break
        if self._bus_type == EMS:
            return model_scheme.get(product_id)

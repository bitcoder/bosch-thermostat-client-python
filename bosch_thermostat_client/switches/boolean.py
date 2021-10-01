from bosch_thermostat_client.const.easycontrol import FALSE, TRUE
from bosch_thermostat_client.const import BINARY, RESULT, URI, VALUE
from bosch_thermostat_client.helper import (
    BoschSingleEntity,
)
from .switch import BaseSwitch


class BooleanSwitch(BaseSwitch, BoschSingleEntity):
    """Boolean switch object."""

    _type = BINARY
    _allowed_types = BINARY

    async def turn_on(self):
        if not self.state:
            await self._turn_action(TRUE)

    async def turn_off(self):
        if self.state:
            await self._turn_action(FALSE)

    async def _turn_action(self, action):
        await self._connector.put(self._data[self.attr_id][URI], action)
        self._data[self.attr_id][RESULT][VALUE] = action

    def check_state(self, value):
        return True if value == TRUE else False
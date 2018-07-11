"""
Update your custom_cards.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_cards
"""
import logging
import os
from datetime import timedelta
import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

__version__ = '0.0.1'

DOMAIN = 'custom_cards'
CONF_AUTO_UPDATE = 'auto_update'

INTERVAL = timedelta(minutes=60)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_AUTO_UPDATE, default='False'): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Set up the component."""
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report them here: https://github.com/custom-components/%s', __version__, __name__.split('.')[1])
    auto_update = config[DOMAIN][CONF_AUTO_UPDATE]
    www_dir = str(hass.config.path("www/"))

    def update_cards_interval(now):
        """Set up recuring update."""
        _update_cards(www_dir)

    def update_cards_service(now):
        """Set up service for manual trigger."""
        _update_cards(www_dir)

    if auto_update == 'True':
        track_time_interval(hass, update_cards_interval, INTERVAL)
    hass.services.register(
        DOMAIN, 'update_cards', update_cards_service)
    return True

def _update_cards(www_dir):
    """DocString"""
    for file in os.listdir(www_dir):
        if file.endswith(".js"):
            card = file.split('.')[0]
            _LOGGER.debug('Downloading new version of %s', card)
            url = 'https://raw.githubusercontent.com/ciotlosm/custom-lovelace/master/' + card + '/' + card + '.js'
            response = requests.get(url)
            if response.status_code == 200:
                with open(www_dir + card + '.js', 'wb') as f:
                    f.write(response.content)
                _LOGGER.debug('%s update sucessful...', card)

            else:
                _LOGGER.debug('%s not found on remote repo, skipping update...', card)

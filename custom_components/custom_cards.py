"""
Update your custom_cards.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_cards
"""
import logging
import os
import subprocess
from datetime import timedelta

import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

__version__ = '1.1.6'

DOMAIN = 'custom_cards'
DATA_CC = 'custom_cards_data'
CONF_AUTO_UPDATE = 'auto_update'

ATTR_CARD = 'card'

INTERVAL = timedelta(days=1)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_AUTO_UPDATE, default=False): cv.boolean,
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

BROWSE_REPO = 'https//github.com/ciotlosm/custom-lovelace/master/'
BASE_REPO = 'https://raw.githubusercontent.com/ciotlosm/custom-lovelace/master/'


def setup(hass, config):
    """Set up the component."""
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report \
                  them here: https://github.com/custom-components/%s', __version__, __name__.split('.')[1])
    auto_update = config[DOMAIN][CONF_AUTO_UPDATE]
    www_dir = str(hass.config.path("www/"))
    lovelace_config = str(hass.config.path("ui-lovelace.yaml"))
    controller = CustomCards(hass, www_dir, lovelace_config)

    def update_cards_service(call):
        """Set up service for manual trigger."""
        controller.update_cards()

    def update_card_service(call):
        """Set up service for manual trigger."""
        controller.update_card(call.data.get(ATTR_CARD))

    track_time_interval(hass, controller.cache_versions, INTERVAL)
    hass.services.register(
        DOMAIN, 'update_cards', update_cards_service)
    hass.services.register(
        DOMAIN, 'update_card', update_card_service)
    hass.services.register(
        DOMAIN, 'check_versions', controller.cache_versions)
    return True


class CustomCards:
    """Custom cards controller."""
    def __init__(self, hass, www_dir, lovelace_config):
        self.hass = hass
        self.www_dir = www_dir
        self.lovelace_config = lovelace_config
        self.cards = None
        self.hass.data[DATA_CC] = {}
        self.cache_versions(None) # Force a cache on startup

    def cache_versions(self, time):
        self.cards = self.get_installed_cards()
        for card in self.cards:
            localversion = self.get_local_version(card)
            remoteversion = self.get_remote_version(card)
            has_update = (localversion != False and remoteversion != False and remoteversion != localversion)
            self.hass.data[DATA_CC][card] = {
                "local": localversion,
                "remote": remoteversion,
                "has_update": has_update,
            }

    def update_cards(self):
        """Update all cards"""
        for card in self.cards:
            if self.hass.data[DATA_CC][card]['has_update']:
                self.update_card(card)

    def update_card(self, card):
        """Update one cards"""
        if card in self.hass.data[DATA_CC]:
            if self.hass.data[DATA_CC][card]['has_update']:
                self.download_card(card)
                self.update_resource_version(card)
                self.hass.data[DATA_CC][card]['local'] = self.hass.data[DATA_CC][card]['remote']
                self.hass.data[DATA_CC][card]['has_update'] = False
                _LOGGER.info('Upgrade of %s from version %s to version %s complete', card, self.hass.data[DATA_CC][card]['local'], self.hass.data[DATA_CC][card]['remote'])
        else:
            _LOGGER.warn('Upgrade failed, no valid card specified %s', card)

    def download_card(self, card):
        """Downloading new card"""
        _LOGGER.debug('Downloading new version of %s', card)
        downloadurl = BASE_REPO + card + '/' + card + '.js'
        response = requests.get(downloadurl)
        if response.status_code == 200:
            with open(self.www_dir + card + '.js', 'wb') as card_file:
                card_file.write(response.content)

    def update_resource_version(self, card):
        """Updating the ui-lovelace file"""
        localversion = self.hass.data[DATA_CC][card]['local']
        remoteversion = self.hass.data[DATA_CC][card]['remote']
        _LOGGER.debug('Updating configuration for %s', card)
        sedcmd = 's/\/'+ card + '.js?v=' + str(localversion) + '/\/'+ card + '.js?v=' + str(remoteversion) + '/'
        _LOGGER.debug('Upgrading card in config from version %s to version %s', localversion, remoteversion)
        subprocess.call(["sed", "-i", "-e", sedcmd, self.lovelace_config])

    def get_installed_cards(self):
        """Get all cards in use from the www dir"""
        _LOGGER.debug('Checking for installed cards in  %s', self.www_dir)
        cards = []
        cards_in_use = []
        for file in os.listdir(self.www_dir):
            if file.endswith(".js"):
                cards.append(file.split('.')[0])
        if len(cards):
            _LOGGER.debug('Checking which cards that are in use in ui-lovelace.yaml')
            for card in cards:
                with open(self.lovelace_config, 'r') as local:
                    for line in local.readlines():
                        if '/' + card + '.js' in line:
                            cards_in_use.append(card)
                            break
            _LOGGER.debug('These cards where found: %s', cards_in_use)
        else:
            _LOGGER.debug('No cards where found. %s', cards)
            cards_in_use = None
        return cards_in_use

    def get_remote_version(self, card):
        """Return the remote version if any."""
        remoteversion = BASE_REPO + card + '/VERSION'
        response = requests.get(remoteversion)
        if response.status_code == 200:
            remoteversion = response.text
            _LOGGER.debug('Remote version of %s is %s', card, remoteversion)
            remoteversion = remoteversion
        else:
            _LOGGER.debug('Could not get the remote version for %s', card)
            remoteversion = False
        return remoteversion

    def get_local_version(self, card):
        """Return the local version if any."""
        cardconfig = ''
        with open(self.lovelace_config, 'r') as local:
            for line in local.readlines():
                if '/' + card + '.js' in line:
                    cardconfig = line
                    break
        if '=' in cardconfig:
            localversion = cardconfig.split('=')[1].split('\n')[0]
            _LOGGER.debug('Local version of %s is %s', card, localversion)
            return localversion
        _LOGGER.debug('Could not get the local version for %s', card)
        return False

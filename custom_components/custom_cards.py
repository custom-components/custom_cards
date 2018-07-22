"""
Update your custom_cards.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_cards
"""
import logging
import os
import subprocess
from datetime import timedelta
import time

import requests
from homeassistant.helpers.event import track_time_interval

__version__ = '2.0.0'

DOMAIN = 'custom_cards'
DATA_CC = 'custom_cards_data'

ATTR_CARD = 'card'

INTERVAL = timedelta(days=1)

_LOGGER = logging.getLogger(__name__)

BROWSE_REPO = 'https//github.com/ciotlosm/custom-lovelace/master/'
VISIT_REPO = 'https://github.com/ciotlosm/custom-lovelace/blob/master/%s/changelog.md'
BASE_REPO = 'https://raw.githubusercontent.com/ciotlosm/custom-lovelace/master/'
VERSION_URL = 'https://raw.githubusercontent.com/custom-cards/information/master/repos.json'

def setup(hass, config):
    """Set up the component."""
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report \
                  them here: https://github.com/custom-components/%s',
                 __version__, __name__.split('.')[1])
    conf_dir = str(hass.config.path())
    controller = CustomCards(hass, conf_dir)

    def update_all_service(call):
        """Set up service for manual trigger."""
        controller.update_all()

    def update_single_service(call):
        """Set up service for manual trigger."""
        controller.update_single(call.data.get(ATTR_CARD))

    track_time_interval(hass, controller.cache_versions, INTERVAL)
    hass.services.register(
        DOMAIN, 'update_all', update_all_service)
    hass.services.register(
        DOMAIN, 'update_single', update_single_service)
    hass.services.register(
        DOMAIN, 'check_all', controller.cache_versions)
    return True


class CustomCards:
    """Custom cards controller."""
    def __init__(self, hass, conf_dir):
        self.hass = hass
        self.conf_dir = conf_dir
        self.cards = None
        self.hass.data[DATA_CC] = {}
        self.cache_versions(None) # Force a cache update on startup

    def cache_versions(self, call):
        """Cache"""
        self.cards = self.get_installed_cards()
        self.hass.data[DATA_CC] = {} # Empty list to start from scratch
        if self.cards:
            for card in self.cards:
                localversion = self.get_local_version(card[0])
                remoteversion = self.get_remote_version(card[0])
                has_update = (localversion != False and remoteversion != False and remoteversion != localversion)
                not_local = (remoteversion != False and not localversion)
                self.hass.data[DATA_CC][card[0]] = {
                    "local": localversion,
                    "remote": remoteversion,
                    "has_update": has_update,
                    "not_local": not_local,
                }
                self.hass.data[DATA_CC]['domain'] = DOMAIN
                self.hass.data[DATA_CC]['repo'] = VISIT_REPO
            self.hass.states.set('sensor.custom_card_tracker', time.time(), self.hass.data[DATA_CC])


    def update_all(self):
        """Update all cards"""
        for card in self.cards:
            if self.hass.data[DATA_CC][card[0]]['has_update']:
                self.update_single(card[0], card[1])
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', card[0])

    def update_single(self, card, card_dir=None):
        """Update one cards"""
        if not card_dir:
            card_dir = self.get_card_dir(card)
        if card in self.hass.data[DATA_CC]:
            if self.hass.data[DATA_CC][card]['has_update']:
                self.download_card(card, card_dir)
                self.update_resource_version(card)
                _LOGGER.info('Upgrade of %s from version %s to version %s complete', card, self.hass.data[DATA_CC][card]['local'], self.hass.data[DATA_CC][card]['remote'])
                self.hass.data[DATA_CC][card]['local'] = self.hass.data[DATA_CC][card]['remote']
                self.hass.data[DATA_CC][card]['has_update'] = False
                self.hass.states.set('sensor.custom_card_tracker', time.time(), self.hass.data[DATA_CC])
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', card)
        else:
            _LOGGER.error('Upgrade failed, no valid card specified %s', card)

    def download_card(self, card, card_dir):
        """Downloading new card"""
        _LOGGER.debug('Downloading new version of %s', card)
        response = requests.get(VERSION_URL)
        if response.status_code == 200:
            downloadurl = response.json()[card]['remote_location']
            download = requests.get(downloadurl)
            if download.status_code == 200:
                with open(self.conf_dir + card_dir + card + '.js', 'wb') as card_file:
                    card_file.write(download.content)

    def update_resource_version(self, card):
        """Updating the ui-lovelace file"""
        localversion = self.hass.data[DATA_CC][card]['local']
        remoteversion = self.hass.data[DATA_CC][card]['remote']
        _LOGGER.debug('Updating configuration for %s', card)
        sedcmd = 's/\/'+ card + '.js?v=' + str(localversion) + '/\/'+ card + '.js?v=' + str(remoteversion) + '/'
        _LOGGER.debug('Upgrading card in config from version %s to version %s', localversion, remoteversion)
        subprocess.call(["sed", "-i", "-e", sedcmd, self.conf_dir + '/ui-lovelace.yaml'])
        _LOGGER.debug("sed -i -e %s %s ", sedcmd, self.conf_dir + '/ui-lovelace.yaml')

    def get_installed_cards(self):
        """Get all cards in use from the www dir"""
        _LOGGER.debug('Checking for installed cards in  %s/www', self.conf_dir)
        cards = []
        cards_in_use = []
        for filenames in os.walk(self.conf_dir + '/www'):
            for file in filenames[2]:
                _LOGGER.debug(file)
                if file.endswith(".js"):
                    cards.append(file.split('.')[0])
        if len(cards):
            _LOGGER.debug('Checking which cards that are in use in ui-lovelace.yaml')
            for card in cards:
                with open(self.conf_dir + '/ui-lovelace.yaml', 'r') as local:
                    for line in local.readlines():
                        if '/' + card + '.js' in line:
                            card_dir = self.get_card_dir(card)
                            cards_in_use.append([card, card_dir])
                            break
            _LOGGER.debug('These cards where found: %s', cards_in_use)
        else:
            _LOGGER.debug('No cards where found. %s', cards)
            cards_in_use = None
        return cards_in_use

    def get_card_dir(self, card):
        """Get card dir"""
        with open(self.conf_dir + '/ui-lovelace.yaml', 'r') as local:
            for line in local.readlines():
                if '/' + card + '.js' in line:
                    card_dir = line.split(': ')[1].split(card + '.js')[0].replace("local", "www")
                    _LOGGER.debug('Found path "%s" for card "%s"', card_dir, card)
                    break
        return card_dir

    def get_remote_version(self, card):
        """Return the remote version if any."""
        response = requests.get(VERSION_URL)
        if response.status_code == 200:
            remoteversion = response.json()[card]['version']
            _LOGGER.debug('Remote version of %s is %s', card, remoteversion)
        else:
            _LOGGER.debug('Could not get the remote version for %s', card)
            remoteversion = False
        return remoteversion

    def get_local_version(self, card):
        """Return the local version if any."""
        cardconfig = ''
        with open(self.conf_dir + '/ui-lovelace.yaml', 'r') as local:
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

    def get_cards(self):
        """Get all available cards"""
        cards = []
        response = requests.get(VERSION_URL)
        if response.status_code == 200:
            for card in response.json():
                cards.append(card)
        else:
            _LOGGER.debug('Could not reach the remote repo')
        _LOGGER.debug(cards)
        return cards

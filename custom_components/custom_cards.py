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

__version__ = '1.0.1'

DOMAIN = 'custom_cards'
CONF_AUTO_UPDATE = 'auto_update'

ATTR_CARD = 'card'

INTERVAL = timedelta(minutes=60)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_AUTO_UPDATE, default='False'): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

BASE_URL = 'https://raw.githubusercontent.com/'
REPO = 'ciotlosm/custom-lovelace/master/'
BASE_REPO = BASE_URL + REPO

def setup(hass, config):
    """Set up the component."""
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report them here: https://github.com/custom-components/%s', __version__, __name__.split('.')[1])
    auto_update = config[DOMAIN][CONF_AUTO_UPDATE]
    www_dir = str(hass.config.path("www/"))
    lovelace_config = str(hass.config.path("ui-lovelace.yaml"))
    data_card = None

    def update_cards_interval(now):
        """Set up recuring update."""
        _update_cards(www_dir, lovelace_config, 'auto', auto_update, data_card)

    def update_cards_service(call):
        """Set up service for manual trigger."""
        data_card = call.data.get(ATTR_CARD)
        _update_cards(www_dir, lovelace_config, 'manual', auto_update, data_card)

        track_time_interval(hass, update_cards_interval, INTERVAL)
    hass.services.register(
        DOMAIN, 'update_cards', update_cards_service)
    return True

def _update_cards(www_dir, lovelace_config, update_type, auto_update, data_card):
    """DocString"""
    if data_card == None:
        cards = get_installed_cards(www_dir)
    else:
        cards = [data_card]
    if cards != None:
        for card in cards:
            localversion = get_local_version(card, lovelace_config)
            if localversion != False:
                remoteversion = get_remote_version(card)
                if remoteversion != False:
                    if localversion != remoteversion:
                        if auto_update == 'True':
                            update_type = 'manual'
                        if update_type == 'manual':
                            download_card(card, www_dir)
                            update_config(lovelace_config, card, localversion, remoteversion)
                            _LOGGER.info('Upgrade of %s from version %s to version %s complete', card, localversion, remoteversion)
                        else:
                            _LOGGER.info("Version %s is available for %s run the service 'custom_cards.update_cards' to upgrade, or visit %s to download manually", remoteversion, card, BASE_REPO)
                    else:
                        _LOGGER.debug('Skipping upgrade of card %s', card)
                else:
                    _LOGGER.debug('Skipping upgrade of card %s', card)
            else:
                _LOGGER.debug('Skipping upgrade of card %s', card)

def get_installed_cards(www_dir):
    """Get all cards in www dir"""
    _LOGGER.debug('Checking for installed cards in  %s', www_dir)
    cards = []
    for file in os.listdir(www_dir):
        if file.endswith(".js"):
            cards.append(file.split('.')[0])
    if len(cards):
        _LOGGER.debug('These cards where found: %s', cards)
        cards = cards
    else:
        _LOGGER.debug('No cards where found. %s', cards)
        cards = None
    return cards

def get_remote_version(card):
    """Return the remote version if any."""
    _LOGGER.debug('Checking remote version of %s', card)
    remoteversion = BASE_REPO + card + '/VERSION'
    response = requests.get(remoteversion)
    if response.status_code == 200:
        remoteversion = response.text
        _LOGGER.debug('Remote version is %s', remoteversion)
        remoteversion = remoteversion
    else:
        _LOGGER.debug('Could not get the remote version for %s', card)
        remoteversion = False
    return remoteversion

def get_local_version(card, lovelace_config):
    """Return the local version if any."""
    _LOGGER.debug('Checking local version of %s', card)
    with open(lovelace_config, 'r') as local:
        for line in local.readlines():
            if '/' + card + '.js' in line:
                cardconfig = line
                break
    if '=' in cardconfig:
        localversion = cardconfig.split('=')[1].split('\n')[0]
        _LOGGER.debug('Local version is %s', localversion)
        return localversion
    else:
        _LOGGER.debug('Could not get the local version for %s', card)
        return False

def download_card(card, www_dir):
    """Downloading new card"""
    _LOGGER.debug('Downloading new version of %s', card)
    downloadurl = BASE_REPO + card + '/' + card + '.js'
    response = requests.get(downloadurl)
    if response.status_code == 200:
        with open(www_dir + card + '.js', 'wb') as card_file:
            card_file.write(response.content)

def update_config(lovelace_config, card, localversion, remoteversion):
    """Updating the ui-lovelace file"""
    _LOGGER.debug('Updating configuration for %s', card)
    sedcmd = 's/\/'+ card + '.js?v=' + str(localversion) + '/\/'+ card + '.js?v=' + str(remoteversion) + '/'
    _LOGGER.debug('Upgrading card in config from version %s to version %s', localversion, remoteversion)
    subprocess.call(["sed", "-i", "-e", sedcmd, lovelace_config])

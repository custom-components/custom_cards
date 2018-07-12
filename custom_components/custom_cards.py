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

__version__ = '1.1.3'

DOMAIN = 'custom_cards'
CONF_AUTO_UPDATE = 'auto_update'
CONF_CARDS = 'cards'

ATTR_CARD = 'card'

INTERVAL = timedelta(minutes=60)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_AUTO_UPDATE, default=False): cv.boolean,
        vol.Optional(CONF_CARDS, default='None'):
            vol.All(cv.ensure_list, [cv.string]),
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

BASE_URL = 'https://raw.githubusercontent.com/'
REPO = 'ciotlosm/custom-lovelace/master/'
BROWSE_REPO = 'https//github.com/' + REPO
BASE_REPO = BASE_URL + REPO

def setup(hass, config):
    """Set up the component."""
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report them here: https://github.com/custom-components/%s', __version__, __name__.split('.')[1])
    auto_update = config[DOMAIN][CONF_AUTO_UPDATE]
    card_list = config[DOMAIN][CONF_CARDS]
    www_dir = str(hass.config.path("www/"))
    lovelace_config = str(hass.config.path("ui-lovelace.yaml"))
    data_card = None

    def update_cards_interval(now):
        """Set up recuring update."""
        _update_cards(www_dir, lovelace_config, data_card, card_list, auto_update)

    def update_cards_service(call):
        """Set up service for manual trigger."""
        data_card = call.data.get(ATTR_CARD)
        _update_cards(www_dir, lovelace_config, data_card, card_list, True)

    track_time_interval(hass, update_cards_interval, INTERVAL)
    hass.services.register(
        DOMAIN, 'update_cards', update_cards_service)
    return True

def _update_cards(www_dir, lovelace_config, data_card, card_list, force_update):
    """Update cards."""
    updates = []
    if data_card == None:
        cards = get_installed_cards(www_dir, lovelace_config, card_list)
    else:
        cards = [data_card]
    if cards != None:
        for card in cards:
            localversion = get_local_version(card, lovelace_config)
            remoteversion = get_remote_version(card)
            if localversion != False and remoteversion != False and remoteversion != localversion:
                if force_update:
                    download_card(card, www_dir)
                    update_config(lovelace_config, card, localversion, remoteversion)
                    _LOGGER.info('Upgrade of %s from version %s to version %s complete', card, localversion, remoteversion)
                else:
                    updates.append(card + ' (' + localversion + '|' +remoteversion + ')')
                    #_LOGGER.info("Version %s is available for %s (currently version %s). Please run the service 'custom_cards.update_cards' to upgrade, or visit %s%s/%s.js to download manually", remoteversion, card, localversion, BASE_REPO, card, card)
            else:
                _LOGGER.debug('Card %s is version %s and remote is version %s, skipping update..', card, localversion, remoteversion)
        if updates:
            _LOGGER.info("Available updates found for cards (localversion|remoteversion) %s. Please run the service 'custom_cards.update_cards' to upgrade, or visit %s to download manually", updates, BROWSE_REPO)

def get_installed_cards(www_dir, lovelace_config, card_list):
    """Get all cards in use from the www dir"""
    _LOGGER.debug('Checking for installed cards in  %s', www_dir)
    cards = []
    cards_in_use = []
    for file in os.listdir(www_dir):
        if file.endswith(".js"):
            cards.append(file.split('.')[0])
    if len(cards):
        _LOGGER.debug('Checking which cards that are in use in ui-lovelace.yaml')
        for card in cards:
            with open(lovelace_config, 'r') as local:
                for line in local.readlines():
                    if '/' + card + '.js' in line:
                        if card in card_list or card_list[0] == 'None':
                            cards_in_use.append(card)
                        break
        _LOGGER.debug('These cards where found: %s', cards_in_use)
    else:
        _LOGGER.debug('No cards where found. %s', cards)
        cards_in_use = None
    return cards_in_use

def get_remote_version(card):
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

def get_local_version(card, lovelace_config):
    """Return the local version if any."""
    cardconfig = None
    with open(lovelace_config, 'r') as local:
        for line in local.readlines():
            if '/' + card + '.js' in line:
                cardconfig = line
                break
    if '=' in cardconfig:
        localversion = cardconfig.split('=')[1].split('\n')[0]
        _LOGGER.debug('Local version of %s is %s', card, localversion)
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

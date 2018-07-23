# custom_component to update custom_cards
***
***
**No more updates are added to this component, use this instead:**\
https://github.com/custom-components/custom_updater
***
***
A component which allows you to update your custom_cards automatically and monitor their versions from the UI. It exposes three services: `custom_cards.update_all`, `custom_cards.update_single` and `custom_cards.check_all`.

To get the best use for this card, use together with [tracker-card](https://github.com/ciotlosm/custom-lovelace/tree/master/tracker-card)\

⚠️ This wil ONLY work if your cards if from:

- https://github.com/ciotlosm/custom-lovelace
- https://github.com/custom-cards


## Installation

To get started put `/custom_components/custom_cards.py`  
here: `<config directory>/custom_components/custom_cards.py` 

## Example configuration

In your `configuration.yaml`:

```yaml
custom_cards:
```

## Debug logging

In your `configuration.yaml`

```yaml
logger:
  default: warn
  logs:
    custom_components.custom_cards: debug
```

## Update single card

You can update a single card by passing which card you want to update to the  `custom_cards.update_single` service.

### From dev-service

Service:
`custom_cards.update_single`

Service Data:

```json
{
  "card":"monster-card"
}
```

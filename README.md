# custom_component to update custom_cards

A component which allows you to update your custom_cards automatically and monitor their versions from the UI. It exposes three services: `custom_cards.update_all`, `custom_cards.update_single` and `custom_cards.check_all`.

To get the best use for this card, use together with [card-tracker](https://github.com/ciotlosm/custom-lovelace/tree/master/card-tracker)\
**To use this card you can _NOT_ set `hide_sensor` to `true`**

⚠️ For now this wil ONLY work if your cards if from https://github.com/ciotlosm/custom-lovelace


## Installation

To get started put `/custom_components/custom_cards.py`  
here: `<config directory>/custom_components/custom_cards.py` 

## Configuration
  
| key | default | required | description
| --- | --- | --- | ---
| **hide_sensor** | False | no | Download and register the sensor used by the [card-tracker](https://github.com/ciotlosm/custom-lovelace/tree/master/card-tracker), can be `True`/`False`

☢️ It is strongly adviced to not have this auto update

## Example

In your `configuration.yaml`:

```yaml
custom_cards:
```

ℹ️ The sensor will get discovered automatically if installation was done correctly.

## Debug logging

In your `configuration.yaml`

```yaml
logger:
  default: warn
  logs:
    custom_components.custom_cards: debug
    custom_components.sensor.custom_cards: debug
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

# custom_component to update custom_cards

[![Version](https://img.shields.io/badge/version-0.0.1-green.svg?style=for-the-badge)](#) [![mantained](https://img.shields.io/maintenance/yes/2018.svg?style=for-the-badge)](#) [![maintainer](https://img.shields.io/badge/maintainer-Joakim%20Sørensen%20%40ludeeus-blue.svg?style=for-the-badge)](#)

A component which allows you to update your custom_cards automatically or with service `custom_cards.update_cards`.

## For now this wil ONLY work if your cards if from https://github.com/ciotlosm/custom-lovelace

To get started put `/custom_components/custom_cards.py`  
here: `<config directory>/custom_components/custom_cards.py`  
  
**Example configuration.yaml:**

```yaml
custom_cards:
  auto_update: 'False'
```

**Configuration variables:**  
  
key | description  
:--- | :---  
**auto_update (Optional)** | Activate auto update of custom_cards, can be `'True'`/`'False'`, default is `'False'`.

## It is strongly adviced to not have this auto update
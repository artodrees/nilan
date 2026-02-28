[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
# Nilan
Nilan integration for Home Assistant

CTS602 supported devices (as typed in HMI menu):

- Comfort light
- VPL 15c
- CompactS
- VP18cCom
- COMFORT
- VP 18c
- VP 18ek
- VP 18cek
- VPL 25c
- COMFORTn
- COMBI 300 N
- COMBI 302
- COMBI 302 T
- VGU180 ek
- CompactP (AIR/GEO)

Majority of functions are supported. If some critical is missing please leave an issue.

If you have CTS700 or another device you will have to help me with that.

## Installation
### Hardware
You must have one interface type installed on your Nilan device for this Integration to work 

#### Supported Interface Types
- ModBus RTU to Modbus TCP Bridge 
- USB to RS485 adaptor

#### Tested Known-to-work Bridge Devices
* USR-TCP232-410S
* Waveshare RS485 TO ETH (B)
* https://github.com/veista/modbus_bridge

### Software
#### Manually
- Copy the nilan folder into your custom_components folder
- Restart HA
- Add Nilan from Integrations

#### HACS
- This integration is available from HACS
- Add Nilan from Integrations

## Issues
1. Before submitting an issue, read the previous <a href="https://github.com/veista/nilan/issues?q=">issues</a>, <a href="https://github.com/veista/nilan/wiki">wiki</a>, <a href="https://github.com/veista/nilan/discussions">discussions</a> and <a href="https://github.com/veista/nilan/releases">release notes</a>.
2. If you have a CTS700 device, it is a long road to get it supported by this integration, open an issue and we will go forward there
3. If you have a CTS602 device and you get a device not supported error during installation:
  - Turn on debug logging for the integration and try installing the integration again. Take note of the debug log and submit it with the issue.
  - Take a picture of the device type plate and submit it with the issue.
  - If you have HMI350T - Touch screen HMI - installed on your device, take a picture of the device info page and submit it with the issue.
  - If you have CTS602 HMI, take a picture of "SHOW DATA" -> "TYPE" and submit it with the issue.
4. On other Issues:
  - Submit the following: Logs, Modbus Version, Device Type - as Shown in the Integration, Device Version - as Shown in the Integration

## Generic Register Read/Write Services

The integration exposes two Home Assistant services that allow reading and writing
arbitrary Modbus registers directly, without needing dedicated entities. This is
useful in automations and from **Developer Tools → Services**.

### `nilan.read_register`

Reads a single raw 16-bit value from an **input** (read-only) or **holding**
(read/write) register and returns it as a service response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | integer | ✓ | Register address (0-based, **not** 40001-style) |
| `table` | `"input"` \| `"holding"` | ✓ | Register table |
| `entry_id` | string | | Config-entry ID; omit when only one Nilan device is configured |

Example automation action:

```yaml
action: nilan.read_register
data:
  table: input
  address: 200   # input_t0_controller (controller board temperature × 100)
response_variable: reg_result
# reg_result["value"] contains the raw 16-bit integer
```

### `nilan.write_register`

Writes a raw 16-bit unsigned integer value (0–65535) to a **holding** register.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | integer | ✓ | Register address (0-based) |
| `value` | integer | ✓ | Raw 16-bit value (0–65535) |
| `entry_id` | string | | Config-entry ID; omit when only one Nilan device is configured |

Example automation action:

```yaml
action: nilan.write_register
data:
  address: 1002  # control_mode_set
  value: 1       # set operation mode to 1
```

> **Note:** Register addresses follow the integration's 0-based convention, not the
> 40001-style offset used in some Modbus documentation. Refer to
> `custom_components/nilan/registers.py` for the full register map.

## Support


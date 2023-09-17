epever = {
        "day_or_night":  {
            "kind": "discrete",
            "value": 0x200c,
            "type": "state"
        },
        "temperature_inside_equipment": {
            "kind": "simple",
            "value": 0x3111,
            "fieldname": "device_temp",
            "type": "state"
        },
        "pv_array_input_voltage": {
            "kind": "simple",
            "value": 0x3100,
            "fieldname": "rated_voltage",
            "type": "counter"
        },
        "pv_array_input_current": {
            "kind": "simple",
            "value": 0x3101,
            "fieldname": "rated_current",
            "type": "counter"
        },
        "pv_array_input_power": {
            "kind": "lowhigh",
            "lsb": 0x3102,
            "msb": 0x3103,
            "fieldname": "pv_rated_watt",
            "type": "counter"
        },
        "battery_rated_voltage": {
            "kind": "simple",
            "value": 0x3104,
            "fieldname": "battery_voltage",
            "type": "counter"
        },
        "battery_rated_current": {
            "kind": "simple",
            "value": 0x3105,
            "fieldname": "battery_current",
            "type": "counter"
        },
        "battery_power": {
            "kind": "lowhigh",
            "lsb": 0x3106,
            "msb": 0x3107,
            "fieldname": "rated_watt",
            "type": "counter"
        },
        "battery_soc": {
            "kind": "simple",
            "value": 0x311A,
            "fieldname": "battery_soc",
            "type": "state"
        },
        "load_voltage": {
            "kind": "simple",
            "value": 0x310C,
            "fieldname": "load_voltage",
            "type": "state"
        },
        "load_current": {
            "kind": "simple",
            "value": 0x310D,
            "fieldname": "load_current",
            "type": "state"
        },
        "load_power": {
            "kind": "lowhigh",
            "lsb": 0x310E,
            "msb": 0x310F,
            "fieldname": "load_watt",
            "type": "state"
        }
    }


epever_statistical = {
    "battery_real_rated_power": 0x311D,
    "battery_status": 0x3200,
    "max_pv_voltage_today": 0x3300,
    "min_pv_voltage_today": 0x3301,
    "max_battery_voltage_today": 0x3302,
    "min_battery_voltage_today": 0x3303,
    "consumed_energy_today": {
        "lsb": 0x3304,
        "msb": 0x3305
    },
    "generated_energy_today": {
        "lsb": 0x330C,
        "msb": 0x330D
    },
    "battery_voltage": 0x331A,
    "battery_current": {
        "lsb": 0x331B,
        "msb": 0x331C
    }
}

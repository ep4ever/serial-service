--
-- This data file is my own setup you must change the device inserts
-- to match your setup.
--

INSERT INTO device (name, port) VALUES('6420an', '/dev/ttyXRUSB1');
INSERT INTO device (name, port) VALUES('3910bp', '/dev/ttyXRUSB0');
INSERT INTO device (name, port) VALUES('3210an', '/dev/ttyXRUSB2');

--
-- FIELD SETUP (no need to change unless you know what you do !)
--

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'temperature_inside_equipment',
	'device_temp',
	'simple',
	'N',
	'0x3111',
	1
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'pv_array_input_voltage',
	'rated_voltage',
	'simple',
	'N',
	'0x3100',
	0
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'pv_array_input_current',
	'rated_current',
	'simple',
	'N',
	'0x3101',
	0
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'pv_array_input_power',
	'pv_rated_watt',
	'lowhigh',
	'N',
	'0x3102|0x3103',
	0
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'battery_rated_voltage',
	'battery_voltage',
	'simple',
	'N',
	'0x3104',
	1
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'battery_rated_current',
	'battery_current',
	'simple',
	'N',
	'0x3105',
	0
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'battery_power',
	'rated_watt',
	'lowhigh',
	'N',
	'0x3106|0x3107',
	0
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'battery_soc',
	'battery_soc',
	'simple',
	'P',
	'0x311A',
	1
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'load_voltage',
	'load_voltage',
	'simple',
	'N',
	'0x310C',
	0
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'load_current',
	'load_current',
	'simple',
	'N',
	'0x310D',
	0
);

INSERT INTO field(label, name, category, format, registeraddr, to_dashboard) VALUES(
	'load_power',
	'load_watt',
	'lowhigh',
	'N',
	'0x310E|0x310F',
	1
);

--
-- DASHBOARD SETUP (no need to change unless you know what you do !)
--

-- batt_soc
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'batt_soc',
	8,
	1,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'batt_soc',
	8,
	2,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'batt_soc',
	8,
	3,
	0
);
-- batt_voltage
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'batt_voltage',
	5,
	1,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'batt_voltage',
	5,
	2,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'batt_voltage',
	5,
	3,
	0
);
-- load
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'load',
	11,
	1,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'load',
	11,
	2,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'load',
	11,
	3,
	0
);

-- temperature
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'temperature',
	1,
	1,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'temperature',
	1,
	2,
	0
);
INSERT INTO dashboard(identifier, field_id, device_id, value) VALUES(
	'temperature',
	1,
	3,
	0
);

-- *************************************************************
-- EDIT this file data section to match you personal setup
-- before issuing bellow instructions
-- *************************************************************
-- To create database use sqlite3 command line tool:
-- At the prompt type: .read $full_path_of_sql_statements_script
-- To see created tables type: .table
-- Use Ctrl+D to exit the command line tool.
-- *************************************************************
-- Start the service in sqlite mode.
-- *************************************************************

CREATE TABLE `device` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT UNIQUE NOT NULL,
  `port` TEXT UNIQUE NOT NULL,
  `baudrate` INTEGER NOT NULL DEFAULT 115200,
  `register_id` INTEGER NOT NULL DEFAULT 1,
  `always_on` INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (`register_id`)
    REFERENCES `register` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
);

CREATE TABLE `register` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT UNIQUE NOT NULL
);

CREATE TABLE `field` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `register_id` INTEGER NOT NULL DEFAULT 1,
  `label` TEXT UNIQUE NOT NULL,
  `name` TEXT UNIQUE NOT NULL,
  `category` TEXT NOT NULL DEFAULT 'simple',
  `format` TEXT NOT NULL DEFAULT 'N',
  `registeraddr` TEXT NOT NULL,
  `datatype` TEXT NOT NULL default 'INTEGER',
  `divider` INT NOT NULL DEFAULT 1,
  `to_dashboard` INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (`register_id`)
    REFERENCES `register` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
);

CREATE TABLE `dashboard` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `identifier` TEXT NOT NULL,
  `field_id` INTEGER,
  `device_id` INTEGER,
  `value` NUMERIC NOT NULL
);

CREATE TABLE `data` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `device_id` INTEGER NOT NULL,
  `field_id` INTEGER NOT NULL,
  `date` DATETIME NOT NULL,
  `value` NUMERIC NOT NULL DEFAULT 0,
   FOREIGN KEY (`device_id`)
    REFERENCES `device` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
   FOREIGN KEY (`field_id`)
    REFERENCES `field` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
);

CREATE INDEX `data_date_idx` ON `data`(date);

CREATE TABLE `consumer_data` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `regkey` TEXT NOT NULL,
  `datestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `value` NUMERIC NOT NULL DEFAULT 0
);
CREATE INDEX `consumer_data_regkey_IDX` ON `consumer_data`(regkey);

-- solardb.diary definition
CREATE TABLE `diary` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `datestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `started_at` DATETIME DEFAULT NULL,
  `ended_at` DATETIME DEFAULT NULL
);
CREATE UNIQUE INDEX `datestamp_UNIQUE_idx` ON `diary`(datestamp);

CREATE TABLE `diary_data` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `diary_id` INTEGER NOT NULL,
  `device_id` INTEGER NOT NULL,
  `field_id` INTEGER NOT NULL,
  `avgval` NUMERIC NOT NULL DEFAULT 0,
  `minval` NUMERIC NOT NULL DEFAULT 0,
  `maxval` NUMERIC NOT NULL DEFAULT 0,
  FOREIGN KEY (`device_id`)
    REFERENCES `device` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  FOREIGN KEY (`diary_id`)
    REFERENCES `diary` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  FOREIGN KEY (`field_id`)
    REFERENCES `field` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
);
CREATE INDEX `fk_diary_data_diary_id_idx` ON `diary_data`(diary_id);
CREATE INDEX `fk_diary_data_device_id_idx` ON `diary_data`(device_id);
CREATE INDEX `fk_diary_data_field_id_idx`  ON `diary_data`(field_id);

-- data content
-- *************************************************************
-- ******************* DATA SECTION ****************************
-- *************************************************************

-- registers
INSERT INTO register(name) VALUES('epever');
INSERT INTO register(name) VALUES('sdm120');

-- devices
insert into device (name, port) values('3210an', '/dev/ttyXRUSB0');
insert into device (name, port) values('6420an', '/dev/ttyXRUSB1');
insert into device (name, port) values('3210an2', '/dev/ttyCH343USB0');
insert into device (name, port, baudrate, register_id, always_on) values('sdm120_etg0', '/dev/ttyUSB1', 9600, 2, 1);
insert into device (name, port, baudrate, register_id, always_on) values('sdm120_etg1', '/dev/ttyUSB0', 9600, 2, 1);

-- sensors (default to register 1: epever)
INSERT INTO field (label,name,category,format,registeraddr,to_dashboard) VALUES
	 ('temperature_inside_equipment','device_temp','simple','N','0x3111',1),
	 ('pv_array_input_voltage','rated_voltage','simple','N','0x3100',0),
	 ('pv_array_input_current','rated_current','simple','N','0x3101',0),
	 ('pv_array_input_power','pv_rated_watt','lowhigh','N','0x3102|0x3103',0),
	 ('battery_rated_voltage','battery_voltage','simple','N','0x3104',1),
	 ('battery_rated_current','battery_current','simple','N','0x3105',0),
	 ('battery_power','rated_watt','lowhigh','N','0x3106|0x3107',0),
	 ('battery_soc','battery_soc','simple','P','0x311A',1),
	 ('load_voltage','load_voltage','simple','N','0x310C',0),
	 ('load_current','load_current','simple','N','0x310D',0),
	 ('load_power','load_watt','lowhigh','N','0x310E|0x310F',1);

-- sensors for TAC1100 (register 2)
INSERT INTO field (label,name,category,format,registeraddr,to_dashboard, register_id, datatype, divider) VALUES
	 ('power_active','power_active','simple','N','0x000c',1,2,'LONG',1),
	 ('total_energy_active','total_energy_active','simple','N','0x0504',1,2,'LONG',100);

-- sensors by device that should always be reported.
-- when no energy is produced values are persisted in this table
INSERT INTO dashboard (id,identifier,field_id,device_id,value) VALUES
	 (1,'batt_soc',8,1,0.0),
	 (2,'batt_soc',8,2,0.0),
	 (3,'batt_soc',8,3,0.0),
	 (4,'batt_voltage',5,1,0.0),
	 (5,'batt_voltage',5,2,0.0),
	 (6,'batt_voltage',5,3,0.0),
	 (7,'load',11,1,0.0),
	 (8,'load',11,2,0.0),
	 (9,'load',11,3,0.0),
	 (10,'temperature',1,1,0.0),
	 (11,'temperature',1,2,0.0),
	 (12,'temperature',1,3,0.0),
   (13,'power_active',12,4,0.0),
	 (14,'total_energy_active',13,4,0.0)
   (15,'power_active',12,5,0.0),
	 (16,'total_energy_active',13,5,0.0)
   ;

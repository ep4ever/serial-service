CREATE TABLE `device` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT UNIQUE NOT NULL,
  `port` TEXT UNIQUE NOT NULL
);

CREATE TABLE `field` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `label` TEXT UNIQUE NOT NULL,
  `name` TEXT UNIQUE NOT NULL,
  `category` TEXT NOT NULL DEFAULT 'simple',
  `format` TEXT NOT NULL DEFAULT 'N',
  `registeraddr` TEXT NOT NULL,
  `to_dashboard` INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE `dashboard` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `identifier` TEXT NOT NULL,
  `field_id` INTEGER NOT NULL,
  `device_id` INTEGER NOT NULL,
  `value` NUMERIC NOT NULL,
   FOREIGN KEY (`device_id`)
	REFERENCES `device` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
   FOREIGN KEY (`field_id`)
    REFERENCES `field` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
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

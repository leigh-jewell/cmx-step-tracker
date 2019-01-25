CREATE TABLE users (
	email varchar(100) NOT NULL PRIMARY KEY,
	salt varchar(255),
	hashed varchar(255),
	admin boolean,
	nickname varchar(255)
);

CREATE TABLE devices (
	mac macaddr NOT NULL PRIMARY KEY,
	owner varchar(100) REFERENCES users (email)
);

CREATE TABLE distance (
        mac macaddr PRIMARY KEY,
        mtrs real,
        floor_id bigint,
        point_1 point,
        point_2 point,
        distance_1to2 real,
        time timestamptz
    );

CREATE TABLE count (
	time timestamp PRIMARY KEY,
	user_count integer DEFAULT 0,
	device_count integer DEFAULT 0,
	notification_count integer DEFAULT 0
);

CREATE TABLE distance_history (
	time timestamptz NOT NULL,
	mac macaddr NOT NULL,
	mtrs real DEFAULT 0.0,
	PRIMARY KEY (time, mac)
);

  CREATE TABLE zone (
    time timestamptz NOT NULL,
    name varchar(255) NOT NULL,
    count integer,
    PRIMARY KEY (time, name)
  );

ALTER TABLE count SET UNLOGGED;
ALTER TABLE distance SET UNLOGGED;
ALTER TABLE distance_history SET UNLOGGED;
ALTER TABLE zone SET UNLOGGED;

CREATE ROLE cmx;
ALTER ROLE cmx LOGIN;
GRANT ALL ON count TO cmx;
GRANT ALL ON devices TO cmx;
GRANT ALL ON distance TO cmx;
GRANT ALL ON distance_history TO cmx;
GRANT ALL ON users TO cmx;
GRANT ALL ON zone TO cmx;
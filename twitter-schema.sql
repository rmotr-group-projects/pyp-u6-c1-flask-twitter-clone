-- sqlite3 database.db < twitter-schema.sql

PRAGMA foreign_keys = ON;

DROP TABLE if exists user;
CREATE TABLE user (
  id INTEGER PRIMARY KEY autoincrement,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  birth_date DATE,
  CHECK (
      length("birth_date") = 10
  )
);

DROP TABLE if exists tweet;
CREATE TABLE tweet (
  id INTEGER PRIMARY KEY autoincrement,
  user_id INTEGER,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  content TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES user(id),
  CHECK(
      typeof("content") = "text" AND
      length("content") <= 140
  )
);

INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (10, "martinzugnoni", "81dc9bdb52d04dc20036dbd8313ed055", "2016-01-26");
INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (11, "ivanzugnoni", "81dc9bdb52d04dc20036dbd8313ed055", "2016-07-06");
INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Hello World!");
INSERT INTO "tweet" ("user_id", "content") VALUES (10, "This is so awesome");
INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Testing twitter clone");
SELECT * FROM tweet;

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
INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (14, "martinzugnoni", "81dc9bdb52d04dc20036dbd8313ed055", "2016-01-26");
INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (11, "ivanzugnoni", "81dc9bdb52d04dc20036dbd8313ed055", "2016-07-06");
INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (12, "doge", "1", "2016-07-06");
INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (13, "doge 🐶🐶🐶🐶", "2", "2016-07-06");

INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Hello World!");
INSERT INTO "tweet" ("user_id", "content") VALUES (10, "This is so awesome");
INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Testing twitter clone");

INSERT INTO "tweet" ("user_id", "content") VALUES (11, "Yo, whats up!");
INSERT INTO "tweet" ("user_id", "content") VALUES (11, "This is so rightous");
INSERT INTO "tweet" ("user_id", "content") VALUES (11, "Testing twitter OUR clone");

INSERT INTO "tweet" ("user_id", "content") VALUES (12, "I love DOGE");
INSERT INTO "tweet" ("user_id", "content") VALUES (12, "DOGEE ♥ ♥ ♥ ");
INSERT INTO "tweet" ("user_id", "content") VALUES (12, "Shibas and corgis are my favourite");


INSERT INTO "tweet" ("user_id", "content") VALUES (13, "I am a cute DOGE");
INSERT INTO "tweet" ("user_id", "content") VALUES (13, "woof woof ");
INSERT INTO "tweet" ("user_id", "content") VALUES (13, "🐶🐶🐶🐶🐶");
INSERT INTO "tweet" ("user_id", "content") VALUES (13, "dude what time is it?");
-- SELECT * FROM tweet;
-- 🐶
  
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

-- INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (10, "martinzugnoni", "81dc9bdb52d04dc20036dbd8313ed055", "2016-01-26");
-- INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (11, "ivanzugnoni", "81dc9bdb52d04dc20036dbd8313ed055", "2016-07-06");
-- INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Hello World!");
-- INSERT INTO "tweet" ("user_id", "content") VALUES (10, "This is so awesome");
-- INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Testing twitter clone");

-- INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (1, "user1", "674f3c2c1a8a6f90461e8a66fb5550ba", "2016-01-26");  --pass = 5678
-- INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (2, "user2", "b20bed91d25a1a6e35455ddbfeab3448", "2016-07-06");  --pass = 9101112
-- INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (3, "user3", "45bf2ae37eec16e85c133cd580e22cd0", "2016-05-11");  --pass = 13141516
-- INSERT INTO "user" ("id", "username", "password", "birth_date") VALUES (4, "user4", "708a2b19de48328eaa8f53537f958419", "2016-12-01");  --pass = 17181920
-- INSERT INTO "tweet" ("user_id", "content") VALUES (1, "I'm user1");
-- INSERT INTO "tweet" ("user_id", "content") VALUES (1, "I'm also user1");
-- INSERT INTO "tweet" ("user_id", "content") VALUES (2, "I'm user2");
-- INSERT INTO "tweet" ("user_id", "content") VALUES (3, "I'm user3");
-- SELECT * FROM tweet;
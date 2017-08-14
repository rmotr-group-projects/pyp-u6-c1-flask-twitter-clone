drop table if exists twitter_user;
create table twitter_user (
  id serial PRIMARY KEY,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  birth_date DATE
);

drop table if exists tweet;
create table tweet (
  id serial PRIMARY KEY,
  user_id INTEGER REFERENCES twitter_user(id),
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  content TEXT NOT NULL
);

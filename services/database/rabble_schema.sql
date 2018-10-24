CREATE TABLE IF NOT EXISTS posts (
  global_id         text    PRIMARY KEY,
  author            text    NOT NULL,
  title             text    NOT NULL,
  body              text    NOT NULL,
  creation_datetime integer NOT NULL
);

CREATE TABLE IF NOT EXISTS local_users (
  handle            text    PRIMARY KEY,
  display_name      text    NOT NULL
);

/* Table for a local follower following a local big_cheese account.
   TODO(iandioch): Look into using foreign keys */
CREATE TABLE IF NOT EXISTS local_follows (
  follower          text    PRIMARY KEY,
  big_cheese        text    NOT NULL
);

/* Add other tables here */

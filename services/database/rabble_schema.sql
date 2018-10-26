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

/* Add other tables here */

CREATE TABLE IF NOT EXISTS posts (
  global_id         text    PRIMARY KEY,
  author            text    NOT NULL,
  title             text    NOT NULL,
  body              text    NOT NULL,
  creation_datetime integer NOT NULL
);
/* Add other tables here */

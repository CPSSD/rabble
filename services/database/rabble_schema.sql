CREATE TABLE IF NOT EXISTS posts (
  global_id         text    PRIMARY KEY,
  author            text    NOT NULL,
  title             text    NOT NULL,
  body              text    NOT NULL,
  creation_datetime integer NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  global_id         text    PRIMARY KEY,
  handle            text    NOT NULL,
  /* host should be null if user is local */
  host              text,
  display_name      text    NOT NULL,
);

/* follower and followed both match global_id in entries in users table. */
CREATE TABLE IF NOT EXISTS follows (
  follower          text    PRIMARY KEY,
  followed          text    NOT NULL
);
/* Add other tables here */

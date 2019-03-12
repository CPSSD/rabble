CREATE TABLE IF NOT EXISTS posts (
  global_id         integer PRIMARY KEY,
  author_id         integer NOT NULL,
  title             text    NOT NULL,
  body              text    NOT NULL,
  creation_datetime integer NOT NULL,
  md_body           text    NOT NULL,
  ap_id             text    NOT NULL,
  likes_count       integer NOT NULL DEFAULT 0,
  shares_count      integer NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
  global_id         integer PRIMARY KEY,
  handle            text    NOT NULL,
  /* host should be null if user is local */
  host              text,
  display_name      text    NOT NULL,
  password          text    NOT NULL,
  bio               text    NOT NULL,
  rss               text,
  /* account_type refers to the account_type enum in the database.proto file.
   * In normal cases, this will be 0, a normal user. */
  private           boolean NOT NULL,
  custom_css        text    NOT NULL DEFAULT '',
  UNIQUE (handle, host)
);

/* follower and followed both match global_id in entries in users table. */
CREATE TABLE IF NOT EXISTS follows (
  follower          integer NOT NULL,
  followed          integer NOT NULL,
  /* State represents the current state of a follow.
   * See the database.proto file for a full list. */
  state             integer NOT NULL,
  PRIMARY KEY (follower, followed)
);

/*
  liker_id is the global_id of a user in the users table
  liked_article_id is the global_id of the article in the posts table.
*/
CREATE TABLE IF NOT EXISTS likes (
  user_id          integer NOT NULL,
  article_id       integer NOT NULL,
  PRIMARY KEY (user_id, article_id)
);

CREATE TABLE IF NOT EXISTS views (
  path             text    NOT NULL,
  user_id          integer NOT NULL,
  datetime         integer NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
  message          text    NOT NULL,
  user_id          integer NOT NULL,
  datetime         integer NOT NULL
);

/*
  user_id is the global_id of the announcing user in the users table
  article_id is the global_id of the shared article in the posts table.
  announce_datetime is the proto timestamp format of the date time the annouce was made
*/
CREATE TABLE IF NOT EXISTS shares (
  user_id           integer NOT NULL,
  article_id        integer NOT NULL,
  announce_datetime integer NOT NULL,
  PRIMARY KEY (user_id, article_id)
);

/* Add other tables here */

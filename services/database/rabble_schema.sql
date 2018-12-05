CREATE TABLE IF NOT EXISTS posts (
  global_id         integer PRIMARY KEY,
  author_id         integer NOT NULL,
  title             text    NOT NULL,
  body              text    NOT NULL,
  creation_datetime integer NOT NULL,
  md_body           text    NOT NULL,
  ap_id             text    NOT NULL,
  likes_count       integer NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
  global_id         integer PRIMARY KEY,
  handle            text    NOT NULL,
  /* host should be null if user is local */
  host              text,
  display_name      text    NOT NULL,
  password          text    NOT NULL,
  bio               text    NOT NULL,
  rss               text
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
  liker_id          integer NOT NULL,
  liked_article_id  integer NOT NULL,
  PRIMARY KEY (liker_id, liked_article_id)
);

/* Add other tables here */


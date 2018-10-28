import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IBlogPost {
  global_id: string;
  author: string;
  title: string;
  body: string;
  creation_datetime: string;
}

const apiURL = "/c2s/feed";

export function SortPosts(b: IBlogPost[]) {
  // TODO: Once creation_datetime is working, sort by that (or global_id)
  b.reverse();
}

export function FixNewlines(b: IBlogPost[]) {
  // TODO: Remove this once we handle body text better
  for (let i = 0; i < b.length; i++) {
    b[i].body = b[i].body.replace(/(?:\r\n|\r|\n)/g, '<br>');
  }
}

export function GetPublicPosts(username= "") {
  const url = username === "" ? apiURL : `${apiURL}/${username}`;
  return new Promise<IBlogPost[]>((resolve, reject) => {
    superagent
      .get(url)
      .set("Accept", "application/json")
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        // Feed will respond with an empty response if no blogs are avaiable.
        let posts = res!.body;
        if (posts === null) {
          posts = [];
        }
        FixNewlines(posts);
        SortPosts(posts);
        resolve(posts);
      });
  });
}

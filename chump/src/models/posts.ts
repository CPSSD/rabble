import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IBlogPost {
  author: string;
  bio: string;
  body: string;
  global_id: number;
  image: string;
  likes_count: number;
  published: string;
  parsed_date: Date;
  title: string;
}

const feedApiURL = "/c2s/feed";
const perUserApiURL = "/c2s/@";

export function SortPosts(b: IBlogPost[]) {
  // convert published string to js datetime obj
  b.map((e: IBlogPost) => {
    e.parsed_date = new Date(e.published);
    if (e.bio === "") {
      e.bio = "Nowadays everybody wanna talk like they got something to say. \
      But nothing comes out when they move their lips; just a bunch of gibberish."
    }
    return e;
  });
  // TODO: Once creation_datetime is working, sort by that (or global_id)
  b.sort((n: IBlogPost, m: IBlogPost) => {
    return m.parsed_date.getTime() - n.parsed_date.getTime();
  });
}

export function PostsAPIPromise(url: string) {
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
        SortPosts(posts);
        resolve(posts);
      });
  });
}

export function GetUsersPosts(username: string) {
  const url = `${perUserApiURL}${encodeURIComponent(username)}`;
  return PostsAPIPromise(url);
}

export function GetSinglePost(username: string, id: string) {
  const url = `${perUserApiURL}${encodeURIComponent(username)}/${id}`;
  return PostsAPIPromise(url);
}

export function GetPublicPosts(username= "") {
  const url = username === "" ? feedApiURL : `${feedApiURL}/${username}`;
  return PostsAPIPromise(url);
}

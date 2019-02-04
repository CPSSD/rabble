import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IBlogPost {
  global_id: number;
  author: string;
  title: string;
  body: string;
  likes_count: number;
  is_liked: boolean;
}

const feedApiURL = "/c2s/feed";
const perUserApiURL = "/c2s/@";

export function SortPosts(b: IBlogPost[]) {
  // TODO: Once creation_datetime is working, sort by that (or global_id)
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

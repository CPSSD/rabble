import * as Promise from "bluebird";
import * as superagent from "superagent";

interface IBlogPost {
  author: string;
  bio: string;
  body: string;
  global_id: number;
  image: string;
  likes_count: number;
  is_liked: boolean;
  published: string;
  title: string;
  is_followed: boolean;
}

export interface IParsedPost extends IBlogPost {
  // parsed_date is a javascript Date object built from published key in
  // IBlogPost
  parsed_date: Date;
}

const feedApiURL = "/c2s/feed";
const perUserApiURL = "/c2s/@";

export function ParsePosts(b: IBlogPost[]) {
  b = b as IParsedPost[];
  // convert published string to js datetime obj
  b.map((e: IParsedPost) => {
    e.parsed_date = new Date(e.published);
    if (e.bio === undefined || e.bio === "") {
      e.bio = "Nowadays everybody wanna talk like they got something to say. \
      But nothing comes out when they move their lips; just a bunch of gibberish.";
    }
    return e;
  });
  return b;
}

export function SortPosts(b: IBlogPost[]) {
  b = ParsePosts(b);
  b.sort((n: IParsedPost, m: IParsedPost) => {
    return m.parsed_date.getTime() - n.parsed_date.getTime();
  });
  return b;
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
        const parsedPosts = SortPosts(posts);
        resolve(parsedPosts);
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
  const url = username === "" ? feedApiURL : `${feedApiURL}/${encodeURIComponent(username)}`;
  return PostsAPIPromise(url);
}

import * as Promise from "bluebird";
import * as request from "superagent";

import { IParsedPost, ParsePosts } from "./posts";

export interface IParsedUser {
  bio: string;
  display_name: string;
  global_id: string;
  handle: string;
  host: string;
  image: string;
  is_followed: boolean;
}

export interface ISearchResponse {
  posts: IParsedPost[];
  users: IParsedUser[];
}

export function CleanUsers(u: IParsedUser[]) {
  u.map((e: IParsedUser) => {
    if (e.display_name === undefined || e.display_name === "") {
      e.display_name = e.handle;
    }
    if (e.bio === undefined || e.bio === "") {
      e.bio = "Nowadays everybody wanna talk like they got something to say. \
      But nothing comes out when they move their lips; just a bunch of gibberish.";
    }
    return e;
  });
  return u;
}

export function SearchAPIPromise(endpoint: string) {
  return new Promise((resolve, reject) => {
    request
      .get(endpoint)
      .set("Accept", "application/json")
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        // Feed will respond with an empty response if no blogs are avaiable.
        let body = res!.body;
        if (body === null) {
          body = {};
        }
        const posts = body!.posts || [];
        const users = body!.users || [];
        const parsedPosts = ParsePosts(posts);
        const cleanedUsers = CleanUsers(users);
        resolve({posts: parsedPosts, users: cleanedUsers});
      });
  });
}

export function SearchRequest(query= "") {
  const endpoint: string = '/c2s/search?query="' + encodeURIComponent(query) + '"';
  return SearchAPIPromise(endpoint);
}

import * as Promise from "bluebird";
import * as request from "superagent";

import { IParsedPost, ParsePosts } from "./posts";

import { CleanUsers, IParsedUser } from './user';

export interface ISearchResponse {
  posts: IParsedPost[];
  users: IParsedUser[];
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

import * as Promise from "bluebird";
import * as request from "superagent";

import { IParsedPost, ParsePosts } from "./posts";

export interface IRecommendedPostsResponse {
  recommendedPosts: IParsedPost[];
}

const recommendPostsApiURL = "/c2s/recommend_posts";

export function RecommendedPostsAPIPromise(endpoint: string) {
  return new Promise((resolve, reject) => {
    request
      .get(endpoint)
      .set("Accept", "application/json")
      .retry(2)
      .end((error, res) => {
        let posts = res!.body;
        if (error && error.status === 501) {
          posts = null;
        } else if (error) {
          reject(error);
          return;
        }

        if (posts === null || posts.results === null || posts.results === undefined) {
          posts = {
            results: [],
          };
        }

        const recommendedPosts = ParsePosts(posts);
        resolve(recommendedPosts);
      });
  });
}

export function GetRecommendedPosts() {
  return RecommendedPostsAPIPromise(recommendPostsApiURL);
}

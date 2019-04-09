import * as Promise from "bluebird";
import * as request from "superagent";

import { CleanUsers, IParsedUser } from "./user";

export interface IRecommendedFollowsResponse {
  recommendedFollows: IParsedUser[];
}

export function RecommendedFollowsAPIPromise(endpoint: string) {
  return new Promise((resolve, reject) => {
    request
      .get(endpoint)
      .set("Accept", "application/json")
      .retry(2)
      .end((error, res) => {
        let body = res!.body;
        if (error && error.status === 501) {
          body = [];
        } else if (error) {
          reject(error);
          return;
        }
        // Feed will respond with a null response if no users are avaiable.
        if (body === null) {
          body = {};
        }
        const users = body! || [];
        const cleanedUsers = CleanUsers(users);
        resolve({recommendedFollows: cleanedUsers});
      });
  });
}

export function GetRecommendedFollows(userId: number) {
  const endpoint: string = "/c2s/" + userId.toString() + "/recommend_follows";
  return RecommendedFollowsAPIPromise(endpoint);
}

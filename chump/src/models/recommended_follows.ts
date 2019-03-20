import * as Promise from "bluebird";
import * as request from "superagent";

export interface IParsedUser {
  bio: string;
  display_name: string;
  global_id: string;
  handle: string;
  host: string;
  image: string;
  is_followed: boolean;
}

export interface IRecommendedFollowsResponse {
  recommendedFollows: IParsedUser[];
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

export function RecommendedFollowsAPIPromise(endpoint: string) {
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
        // Feed will respond with a null response if no users are avaiable.
        let body = res!.body;
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
  const endpoint: string = "/c2s/@" + userId.toString() + "/recommend_follows";
  return RecommendedFollowsAPIPromise(endpoint);
}

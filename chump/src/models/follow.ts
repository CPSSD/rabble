import * as request from "superagent";

interface ICreateFollowPostBody {
  followed: string;
  follower: string;
}

export function CreateFollow(username: string, followedUsername: string) {
  const endpoint: string = "/c2s/follow";
  const postBody: ICreateFollowPostBody = {
    followed: followedUsername,
    follower: username,
  };
  return request.post(endpoint)
    .set("Content-Type", "application/json")
    .send(postBody)
    .retry(2);
}

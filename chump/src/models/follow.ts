import * as request from "superagent";

interface ICreateFollowPostBody {
  follower: string;
  followed: string;
}

export function CreateFollow(username: string, followedUsername: string) {
  const endpoint: string = "/c2s/follow";
  const postBody: ICreateFollowPostBody = {
    follower: username,
    followed: followedUsername,
  };
  return request.post(endpoint)
    .set("Content-Type", "application/json")
    .send(postBody)
    .retry(2);
}

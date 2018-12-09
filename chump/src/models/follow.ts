import * as Promise from "bluebird";
import * as request from "superagent";

interface ICreateFollowPostBody {
  followed: string;
  follower: string;
}

interface ICreateRssFollowPostBody {
  feed_url: string;
  follower: string;
}

export function CreateFollow(username: string, followedUsername: string) {
  const endpoint: string = "/c2s/follow";
  const postBody: ICreateFollowPostBody = {
    followed: followedUsername,
    follower: username,
  };
  return new Promise((resolve, reject) => {
    request
      .post(endpoint)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .send(postBody)
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        resolve(res);
      });
  });
}

export function CreateRssFollow(username: string, rssUrl: string) {
  const endpoint: string = "/c2s/rss_follow";
  const postBody: ICreateRssFollowPostBody = {
    feed_url: rssUrl,
    follower: username,
  };
  return new Promise((resolve, reject) => {
    request
      .post(endpoint)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .send(postBody)
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        resolve(res);
      });
  });
}

export interface IPendingFollow {
  handle: string;
  host?: string;
}

export interface IPendingFollows {
  followers?: IPendingFollow[];
}

export function GetPendingFollows() {
  const url = "/c2s/follows/pending";
  return new Promise<IPendingFollows>((resolve, reject) => {
    request
      .post(url)
      .set("Accept", "application/json")
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        const succ = res!.body;
        if (succ === null) {
          reject("could not parse result");
        }
        resolve(succ as IPendingFollows);
      });
  });
}

export function AcceptFollow(handle: string, follower: IPendingFollow) {
  const url = "/c2s/follows/accept";
  const postBody = {
    follower,
    handle,
  };
  return new Promise<IPendingFollows>((resolve, reject) => {
    request
      .post(url)
      .retry(2)
      .send(postBody)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      });
  });
}

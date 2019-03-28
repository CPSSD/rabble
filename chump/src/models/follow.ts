import * as Promise from "bluebird";
import * as request from "superagent";

interface ICreateFollowPostBody {
  followed: string;
  follower: string;
}

interface IUnfollowPostBody {
  followed: string;
  follower: string;
}

interface ICreateRssFollowPostBody {
  feed_url: string;
  follower: string;
}

function fullyQualifyUsername(handle: string, host: string) {
  let fullUsername: string = handle;
  if (host !== null && host !== "" && typeof host !== "undefined") {
    fullUsername = handle + "@" + host;
  }
  return fullUsername;
}

export function CreateFollow(username: string, followedHandle: string, followedHost: string) {
  const endpoint: string = "/c2s/follow";
  const followedUser = fullyQualifyUsername(followedHandle, followedHost);
  const postBody: ICreateFollowPostBody = {
    followed: followedUser,
    follower: username,
  };
  return new Promise((resolve, reject) => {
    request
      .post(endpoint)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .send(postBody)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        resolve(res);
      });
  });
}

export function Unfollow(username: string, followedHandle: string, followedHost: string) {
  const followedUsername = fullyQualifyUsername(followedHandle, followedHost);
  const endpoint: string = "/c2s/unfollow";
  const postBody: IUnfollowPostBody = {
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

export function AcceptFollow(handle: string, follower: IPendingFollow, isAccepted: boolean) {
  const url = "/c2s/follows/accept";
  const postBody = {
    follower,
    handle,
    is_accepted: isAccepted,
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

export interface IFollowUser {
  handle: string;
  host: string | undefined;
  display_name: string;
}

export interface IFollowers {
  results: IFollowUser[];
}

export function GetFollowers(username: string) {
  const url: string = "/c2s/@" + username + "/followers";
  return GetFollows(url, username);
}

export function GetFollowing(username: string) {
  const url: string = "/c2s/@" + username + "/following";
  return GetFollows(url, username);
}

function GetFollows(url: string, username: string) {
  return new Promise<IFollowUser[]>((resolve, reject) => {
    request
      .get(url)
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        const r = res!.body as IFollowers;
        if (r === null) {
          reject("Could not parse result");
        }
        if (r.results === undefined || r.results === null) {
          resolve([] as IFollowUser[]);
        } else {
          resolve(r.results as IFollowUser[]);
        }
      });
  });
}

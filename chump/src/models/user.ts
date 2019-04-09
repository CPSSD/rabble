import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IUser {
  global_id: number;
  handle: string;
  host: string;
  bio: string;
  display_name: string;
}

export interface IUserDetails extends IUser {
  private: {
    value?: boolean;
  };
  custom_css: string;
}

export interface IParsedUser extends IUser {
  image: string;
  is_followed: boolean;
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

export function GetUserInfo(username: string) {
  const url = "/c2s/@" + username + "/details";
  return new Promise<IUserDetails>((resolve, reject) => {
    superagent
      .post(url)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }

        const details = res!.body;
        if (details === null) {
          reject(new Error("could not get current user details"));
          return;
        }
        resolve(details);
      });
  });
}

import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IParsedUser {
  global_id: number;
  handle: string;
  host: string;
  bio: string;
  display_name: string;
  is_followed: boolean;
  private: {
    value?: boolean;
  };
  custom_css: string;
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
  return new Promise<IParsedUser>((resolve, reject) => {
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

export interface IEditUserResult {
  error: string;
  success: boolean;
}

export function EditUserPromise(
  bio: string, displayName: string,
  currentPassword: string,  newPassword: string,
  privateAccount: boolean,
  customCss: string,
) {
  const url = "/c2s/update/user";
  const postBody = {
    bio,
    current_password: currentPassword,
    custom_css: customCss,
    display_name: displayName,
    new_password: newPassword,
    private: {
      value: privateAccount,
    },
  };
  return new Promise<IEditUserResult>((resolve, reject) => {
    superagent
      .post(url)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .send(postBody)
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        let succ = res!.body;
        if (succ === null) {
          succ = {
            error: "Error parsing response",
            success: false,
          };
        }
        resolve(succ);
      });
  });
}

export function EditUserProfilePicPromise(profilePic: File) {
  const url = "/c2s/update/user_pic";
  return new Promise<IEditUserResult>((resolve, reject) => {
    superagent
      .post(url)
      .set("Accept", "application/json")
      .attach("profile_pic", profilePic)
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        let succ = res!.body;
        if (succ === null) {
          succ = {
            error: "Error parsing response",
            success: false,
          };
        }
        resolve(succ);
      });
  });
}

export interface ILoginResult {
  success: boolean;
  user_id: number;
}

export function GetLoginPromise(handle: string, password: string) {
  const url = "/c2s/login";
  const postBody = { handle, password };
  return new Promise<ILoginResult>((resolve, reject) => {
    superagent
      .post(url)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .send(postBody)
      .retry(2)
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        let succ = res!.body;
        if (succ === null) {
          succ = { success: false };
        }
        resolve(succ);
      });
  });
}

export interface ILogoutResult {
  success: boolean;
}

export function GetLogoutPromise() {
  const url = "/c2s/logout";
  return new Promise<ILogoutResult>((resolve, reject) => {
    superagent
      .get(url)
      .set("Accept", "application/json")
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        let succ = res!.body;
        if (succ === null) {
            succ = { success: false };
        }
        resolve(succ);
      });
  });
}

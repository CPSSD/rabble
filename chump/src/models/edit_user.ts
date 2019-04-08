import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IEditUserResult {
  error: string;
  success: boolean;
}

export interface IUserDetails {
  custom_css: string;
  handle: string;
  host: string;
  global_id: number;
  bio: string;
  private: {
    value?: boolean;
  };
  display_name: string;
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

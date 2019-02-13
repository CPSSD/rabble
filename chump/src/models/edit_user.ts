import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IEditUserResult {
  error: string;
  success: boolean;
}

export function GetUserInfo() {
  const url = "/c2s/details/user";
  return new Promise<IEditUserResult>((resolve, reject) => {
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
        console.log(res.body);
        resolve();
      });
  });
}

export function EditUserPromise(
  bio: string, displayName: string,
  currentPassword: string,  newPassword: string,
  privateAccount: boolean,
) {
  const url = "/c2s/update/user";
  const postBody = {
    bio,
    current_password: currentPassword,
    display_name: displayName,
    new_password: newPassword,
    private: privateAccount,
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

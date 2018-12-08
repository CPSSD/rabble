import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IEditUserResult {
  error: string;
  success: boolean;
}

export function EditUserPromise(bio: string, displayName: string,
                                currentPassword: string,  newPassword: string) {
  const url = "/c2s/update/user";
  const postBody = {
    bio,
    current_password: currentPassword,
    display_name: displayName,
    new_password: newPassword,
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

import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IRegisterResult {
  error: string;
  success: boolean;
  user_id: number;
}

export function GetRegisterPromise(handle: string,
                                   password: string,
                                   displayName: string,
                                   bio: string) {
  const url = "/c2s/register";
  const postBody = { handle, password, displayName, bio };
  return new Promise<IRegisterResult>((resolve, reject) => {
    superagent
      .post(url)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .send(postBody)
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

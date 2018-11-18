import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface ILoginResult {
  success: boolean;
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

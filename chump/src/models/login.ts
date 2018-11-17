import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface ILoginResult {
  success: boolean;
}

export function GetLoginPromise(handle: string, password: string) {
  const url = `/c2s/login?handle=${handle}&password=${password}`
  return new Promise<ILoginResult>((resolve, reject) => {
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
          succ = {'success': false}
        }
        resolve(succ);
      });
  });
}


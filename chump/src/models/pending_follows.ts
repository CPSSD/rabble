import * as Promise from "bluebird";
import * as superagent from "superagent";

export interface IPendingFollow {
  handle: string;
  host?: string;
}

export interface IPendingFollows {
  followers: IPendingFollow[];
}

export function GetPendingFollows() {
  const url = "/c2s/follows/pending";
  return new Promise<IPendingFollows>((resolve, reject) => {
    superagent
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

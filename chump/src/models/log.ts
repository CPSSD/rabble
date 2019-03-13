import * as request from "superagent";

interface ILogBody {
  message: string;
}

export function SendLog(message: string) {
  const endpoint: string = "/c2s/add_log";
  const postBody: ILogBody = {message};
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

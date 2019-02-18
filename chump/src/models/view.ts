import * as request from "superagent";

interface IViewBody {
  path: string;
}

export function SendView(path: string) {
  const endpoint: string = "/c2s/track_view";
  const postBody: IViewBody = {
    path: path,
  };
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

import * as request from "superagent";

interface ILikePostBody {
  article_id: number;
}

export function SendLike(article_id: number) {
  const endpoint: string = "/c2s/like";
  const postBody: ILikePostBody = {
    article_id,
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


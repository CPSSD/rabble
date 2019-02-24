import * as request from "superagent";

interface ILikePostBody {
  article_id: number;
  is_liked: boolean;
}

export function SendLike(articleId: number, isLiked: boolean) {
  const endpoint: string = "/c2s/like";
  const postBody: ILikePostBody = {
    article_id: articleId,
    is_liked: isLiked,
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

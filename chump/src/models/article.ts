import * as Promise from "bluebird";
import * as request from "superagent";

interface ICreateArticlePostBody {
  author: string;
  body: string;
  creation_datetime: string;
  title: string;
  tags: string[];
}

export function CreateAPIPromise(endpoint: string, postBody: ICreateArticlePostBody) {
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

export function CreateArticle(username: string, title: string, blogText: string, tags: string[]) {
  const endpoint: string = "/c2s/create_article";
  const createdTime: string = new Date().toISOString();
  const postBody: ICreateArticlePostBody = {
    author: username,
    body: blogText,
    creation_datetime: createdTime,
    tags,
    title,
  };
  return CreateAPIPromise(endpoint, postBody);
}

export function EditArticle(article_id: string, title: string, blogText: string, tags: string[]) {
  // TODO(CianLR): Send edit request.
  alert("Sending edit");
}

export function CreatePreview(username: string, title: string, blogText: string) {
  const endpoint: string = "/c2s/preview_article";
  const createdTime: string = new Date().toISOString();
  const postBody: ICreateArticlePostBody = {
    author: username,
    body: blogText,
    creation_datetime: createdTime,
    tags: [],
    title,
  };
  return CreateAPIPromise(endpoint, postBody);
}

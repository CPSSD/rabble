import * as request from "superagent";

interface ICreateArticlePostBody {
  author: string;
  body: string;
  creation_datetime: string;
  title: string;
}

export function CreateArticle(username: string, title: string, blogText: string) {
  const endpoint: string = "/c2s/create_article";
  const createdTime: string = new Date().toISOString();
  const postBody: ICreateArticlePostBody = {
    author: username,
    body: blogText,
    creation_datetime: createdTime,
    title,
  };
  return request.post(endpoint)
    .set("Content-Type", "application/json")
    .send(postBody)
    .retry(2);
}

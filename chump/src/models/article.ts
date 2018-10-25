import * as request from "superagent";

export function CreateArticle(username: string, title: string, blogText: string) {
  const endpoint: string = "/c2s/@" + username + "/create_article";
  const createdTime: string = new Date().toISOString();
  const postBody: object = {
    author: username,
    body: blogText,
    creation_datetime: createdTime,
    title,
  };
  return request.post(endpoint)
    .set("Content-Type", "application/json")
    .send(postBody)
    .retry(2);
};

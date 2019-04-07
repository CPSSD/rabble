import * as Promise from "bluebird";
import * as request from "superagent";

import { PartialResponse } from "./common";

interface ICreateArticlePostBody {
  body: string;
  creation_datetime: string;
  summary: string;
  title: string;
  tags: string[];
}

interface IEditArticlePostBody {
  article_id: number;
  body: string;
  summary: string;
  title: string;
  tags: string[];
}

export function CreateAPIPromise(endpoint: string, postBody: ICreateArticlePostBody) {
  return new Promise<PartialResponse>((resolve, reject) => {
    request
      .post(endpoint)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json")
      .send(postBody)
      .end((error, res) => {
        if (error) {
          return reject(error);
        }

        return resolve(res);
      });
  });
}

export function CreateArticle(title: string, blogText: string, tags: string[], summary: string) {
  const endpoint: string = "/c2s/create_article";
  const createdTime: string = new Date().toISOString();
  const postBody: ICreateArticlePostBody = {
    body: blogText,
    creation_datetime: createdTime,
    summary,
    tags,
    title,
  };
  return CreateAPIPromise(endpoint, postBody);
}

export function EditArticle(articleId: number, title: string, blogText: string,
                            tags: string[], summary: string) {
    const endpoint: string = "/c2s/edit_article";
    const postBody: IEditArticlePostBody = {
      article_id: articleId,
      body: blogText,
      summary,
      tags,
      title,
    };
    return new Promise((resolve, reject) => {
      request
        .post(endpoint)
        .set("Content-Type", "application/json")
        .set("Accept", "application/json")
        .send(postBody)
        .end((error, res) => {
          if (error) {
            reject(error);
            return;
          }
          resolve(res);
        });
  });
}

export function CreatePreview(title: string, blogText: string) {
  const endpoint: string = "/c2s/preview_article";
  const createdTime: string = new Date().toISOString();
  const postBody: ICreateArticlePostBody = {
    body: blogText,
    creation_datetime: createdTime,
    summary: "",
    tags: [],
    title,
  };
  return CreateAPIPromise(endpoint, postBody);
}

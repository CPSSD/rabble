import * as React from "react";
import { RouteProps } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { EditArticle } from "../models/article";
import { GetSinglePost, IParsedPost } from "../models/posts";
import { CreateArticleForm } from "./create_article_form";

interface IEditProps extends RouteProps {
  match: {
    params: {
      article_id: string,
    },
  };
  username: string;
}

export const Edit: React.StatelessComponent<IEditProps> = (props) => {
  const fillArticle = (updateFunc: any) => {
    GetSinglePost(props.match.params.article_id)
      .then((posts: IParsedPost[]) => {
        if (posts.length > 0) {
          const p = posts[0];
          const tags = typeof(p.tags) === "undefined" ? [] : p.tags;
          updateFunc(p.title, p.md_body, tags, p.summary);
        }
      })
      .catch(() => alert("Could not prefill post details"));
  };
  const onSubmit = (title: string, text: string, tags: string[], summary: string) => {
    return EditArticle(
      parseInt(props.match.params.article_id, 10),
      title,
      text,
      tags,
      summary,
    );
  };
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
         <CreateArticleForm
           username={props.username}
           prefillState={fillArticle}
           onSubmit={onSubmit}
           successMessage={config.edit_success}
         />
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

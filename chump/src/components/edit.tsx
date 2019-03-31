import * as React from "react";
import { RouteProps } from "react-router-dom";

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
          updateFunc(p.title, p.md_body, p.tags, p.summary);
        }
      })
      .catch(() => alert("Could not prefill post details"));
  };
  const onSubmit = (title: string, text: string, tags: string[]) => {
    return EditArticle(
      props.match.params.article_id,
      title,
      text,
      tags,
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
         />
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

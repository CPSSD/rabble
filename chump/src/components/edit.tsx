import * as React from "react";
import { RouteProps } from "react-router-dom";

import { EditArticle } from "../models/article";
import { CreateArticleForm } from "./create_article_form";

interface IEditProps extends RouteProps {
  match: {
    params: {
      article_id: string,
    },
  };
  username: string;
};

export const Edit: React.StatelessComponent<IEditProps> = (props) => {
  const pre = (state: any, props: any) => {
    return {
      title: "test title",
      blogText: "my blog",
      tags: ["a", "b", "c"],
    }
  }
  const onSubmit = (_: string, title: string, text: string, tags: string[]) => {
    return EditArticle(
      props.match.params.article_id,
      title,
      text,
      tags,
    );
  }
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <CreateArticleForm
          username={props.username}
          prefillState={pre}
          onSubmit={onSubmit}
        />
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

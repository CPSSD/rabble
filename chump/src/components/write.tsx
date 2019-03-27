import * as React from "react";

import { CreateArticle } from "../models/article";
import { CreateArticleForm, IFormProps, IFormState } from "./create_article_form";

interface IWriteProps {
  username: string;
}

export const Write: React.StatelessComponent<IWriteProps> = (props) => {
  const pre = (props: any, state: any) => {
    console.log("Ayyy");
    return state;
  };
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <CreateArticleForm
          username={props.username}
          prefillState={pre}
          onSubmit={CreateArticle}
        />
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

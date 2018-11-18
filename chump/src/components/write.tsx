import * as React from "react";

import { CreateArticleForm, IFormProps } from "./create_article_form";

export const Write: React.StatelessComponent<IFormProps> = (props) => {
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <CreateArticleForm {...props}/>
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

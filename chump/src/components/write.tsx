import * as React from "react";
import { Link } from "react-router-dom";

import CreateArticleForm from "./create_article_form";

export const Write: React.StatelessComponent<{}> = () => {
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <CreateArticleForm/>
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

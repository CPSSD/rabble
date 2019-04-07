import * as React from "react";

import * as config from "../../rabble_config.json";
import { CreateArticle } from "../models/article";
import { CreateArticleForm } from "./create_article_form";

interface IWriteProps {
  username: string;
}

export const Write: React.StatelessComponent<IWriteProps> = (props) => {
  const prefillState = (_: any) => { return; };
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <CreateArticleForm
          username={props.username}
          prefillState={prefillState}
          onSubmit={CreateArticle}
          successMessage={config.write_success}
        />
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

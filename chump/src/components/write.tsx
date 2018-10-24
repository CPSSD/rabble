import * as React from "react";
import { Link } from "react-router-dom";

import CreatePostForm from "./create_post_form";

export const Write: React.StatelessComponent<{}> = () => {
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <CreatePostForm/>
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

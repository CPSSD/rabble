import * as React from "react";
import { Link } from "react-router-dom";

import { FollowForm, IFormProps } from "./follow_form";

export const Follow: React.StatelessComponent<IFormProps> = (props) => {
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <FollowForm {...props}/>
        <p>Yo</p>
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

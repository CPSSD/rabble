import * as React from "react";
import { Link } from "react-router-dom";

import { FollowForm, IFormProps } from "./follow_form";
import { RecommendedFollows } from "./recommended_follows";

export const Follow: React.StatelessComponent<IFormProps> = (props) => {
  return (
    <div>
      <div>
        <div className="pure-u-1-5"/>
        <div className="pure-u-3-5 center-form">
          <FollowForm {...props}/>
        </div>
      </div>
      <br/>
      <div>
        <RecommendedFollows {...props}/>
      </div>
    </div>
  );
};

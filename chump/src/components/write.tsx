import * as React from "react";
import { Link } from "react-router-dom";

export const Write: React.StatelessComponent<{}> = () => {
  return (
    <div>
      <div className="pure-u-1-5"/>
      <div className="pure-u-3-5 center-form">
        <form className="pure-form pure-form-aligned">
          <div className="pure-control-group">
            <input type="text" className="pure-input-1-2" placeholder="Username"/>
          </div>
          <div className="pure-control-group">
            <input type="text" className="pure-input-1-2" placeholder="Title"/>
            <textarea className="pure-input-1 blog-input" placeholder="Start here"></textarea>
          </div>
          <button type="submit" className="pure-button pure-input-1-3 pure-button-primary">Post</button>
        </form>
      </div>
      <div className="pure-u-1-5"/>
    </div>
  );
};

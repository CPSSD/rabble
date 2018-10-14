import * as React from "react";
import { Link } from 'react-router-dom';

export const Home: React.StatelessComponent<{}> = () => {
  return (
    <div>
      <div className="pure-u-1-5"></div>
      <div className="pure-u-3-5">
        <h4>Your blog post could be here!</h4>
        <p>Check out our <Link to="/about">about</Link> page for more info!</p>
      </div>
    </div>
  );
}

import * as React from "react";
import { Link } from "react-router-dom";

export const Header: React.StatelessComponent<{}> = () => {
  return (
    <div className="pure-g">
      <div className="pure-u-1-3"/>
      <div className="pure-u-1-3 centre-brand">
        <Link to="/" className="brand">Rabble</Link>
      </div>
      <div className="pure-u-1-3">
        <div className="pure-menu pure-menu-horizontal">
          <ul className="pure-menu-list right-menu">
            <li className="pure-menu-item">
              <Link to="/write" className="pure-menu-link">Write</Link>
            </li>
            <li className="pure-menu-item">
              <Link to="/login" className="pure-menu-link">Login</Link>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

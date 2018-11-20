import * as React from "react";
import { Link } from "react-router-dom";

interface IHeaderProps {
  username: string;
}

export const Header: React.StatelessComponent<IHeaderProps> = (props) => {

  let Login = (
    <li className="pure-menu-item">
      <Link to="/login" className="pure-menu-link">Login</Link>
    </li>
  );

  let RegisterOrLogout = (
    <li className="pure-menu-item">
      <Link to="/register" className="pure-menu-link">Register</Link>
    </li>
  );

  let Feed: JSX.Element | boolean = false;
  let Follow: JSX.Element | boolean = false;

  if (props.username !== "") {
    Login = (
      <li className="pure-menu-item">
        <Link
          to={`/@${props.username}`}
          className="pure-menu-link"
        >
          {props.username}
        </Link>
      </li>
    );
    RegisterOrLogout = (
      <li className="pure-menu-item">
        <Link to="/logout" className="pure-menu-link">Logout</Link>
      </li>
    );
    Feed = (
        <li className="pure-menu-item">
          <Link to="/feed" className="pure-menu-link">Feed</Link>
        </li>
    );
    Follow = (
        <li className="pure-menu-item">
          <Link to="/follow" className="pure-menu-link">Follow</Link>
        </li>
    );
  }

  return (
    <div className="pure-g topnav">
      <div className="pure-u-5-24"/>
      <div className="pure-u-1-4 centre-brand">
        <Link to="/" className="brand">Rabble</Link>
      </div>
      <div className="pure-u-1-24"/>
      <div className="pure-u-3-24">
        <div className="pure-menu pure-menu-horizontal">
          <ul className="pure-menu-list">
            <li className="pure-menu-item">
              <Link to="/write" className="pure-menu-link">Write</Link>
            </li>
            {Follow}
            {Feed}
            {Login}
            {RegisterOrLogout}
          </ul>
        </div>
      </div>
    </div>
  );
};

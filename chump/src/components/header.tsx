import * as React from "react";
import { Link } from "react-router-dom";

interface IHeaderProps {
  username: string;
}

interface IHeaderState {
  display: string;
}

export class Header extends React.Component<IHeaderProps, IHeaderState> {
  constructor(props: IHeaderProps) {
    super(props);

    this.state = {
      display: "none",
    };

    this.toggleDropdown = this.toggleDropdown.bind(this);
    this.renderMenu = this.renderMenu.bind(this);
    this.resetDropdown = this.resetDropdown.bind(this);
  }

  public render() {
    const Login = (
      <li className="pure-menu-item">
        <Link to="/login" className="pure-menu-link">Login</Link>
      </li>
    );

    const RegisterOrLogout = (
      <li className="pure-menu-item">
        <Link to="/register" className="pure-menu-link">Register</Link>
      </li>
    );

    let Menu = (
      <ul className="pure-menu-list home-menu">
        {Login}
        {RegisterOrLogout}
      </ul>
    );

    if (this.props.username !== "") {
      Menu = this.renderMenu();
    }
    return (
      <div className="pure-g topnav">
        <div className="pure-u-1-24"/>
        <div className="pure-u-6-24 centre-brand">
          <Link to="/" className="brand" onClick={this.resetDropdown}>Rabble</Link>
        </div>
        <div className="pure-u-13-24"/>
        <div className="pure-u-3-24">
          <div className="pure-menu pure-menu-horizontal">
            {Menu}
          </div>
        </div>
        <div className="pure-u-1-24"/>
      </div>
    );
  }

  private renderMenu() {
    const UserMenu = (
      <li className="pure-menu-item pure-menu-has-children">
        <button onClick={this.toggleDropdown} className="button-link pure-menu-link">{this.props.username}</button>
        <ul id="dropdown" className="menu-dropdown pure-menu-children" style={{display: this.state.display}}>
          <li className="pure-menu-item">
            <Link to={`/@${this.props.username}`} className="pure-menu-link" onClick={this.resetDropdown}>
              Profile
            </Link>
          </li>
          <li className="pure-menu-item">
            <Link to="/follow" className="pure-menu-link" onClick={this.resetDropdown}>
              Follow
            </Link>
          </li>
          <li className="pure-menu-item">
            <Link to="/logout" className="pure-menu-link" onClick={this.resetDropdown}>
              Logout
            </Link>
          </li>
        </ul>
      </li>
    );
    const Feed = (
        <li className="pure-menu-item">
          <Link to="/feed" className="pure-menu-link" onClick={this.resetDropdown}>Feed</Link>
        </li>
    );
    const Write = (
      <li className="pure-menu-item">
        <Link to="/write" className="pure-menu-link" onClick={this.resetDropdown}>Write</Link>
      </li>
    );
    return (
      <ul className="pure-menu-list home-menu">
        {Feed}
        {Write}
        {UserMenu}
      </ul>
    );
  }

  private toggleDropdown(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    let target = "none";
    if (this.state.display === "none") {
      target = "inherit";
    }
    this.setState({
      display: target,
    });
  }

  private resetDropdown(event: React.MouseEvent<HTMLAnchorElement>) {
    this.setState({
      display: "none",
    });
  }
}

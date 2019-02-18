import * as React from "react";
import { Search } from "react-feather";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";

interface IHeaderProps {
  username: string;
}

interface IHeaderState {
  display: string;
  query: string;
}

export class Header extends React.Component<IHeaderProps, IHeaderState> {
  constructor(props: IHeaderProps) {
    super(props);

    this.state = {
      display: "none",
      query: "",
    };

    this.toggleDropdown = this.toggleDropdown.bind(this);
    this.handleSearchInputChange = this.handleSearchInputChange.bind(this);
    this.handleSearchSubmit = this.handleSearchSubmit.bind(this);
    this.renderMenu = this.renderMenu.bind(this);
    this.resetDropdown = this.resetDropdown.bind(this);
  }

  public render() {
    const Login = (
      <li className="pure-menu-item">
        <Link to="/login" className="pure-menu-link">{config.login_text}</Link>
      </li>
    );

    const RegisterOrLogout = (
      <li className="pure-menu-item">
        <Link to="/register" className="pure-menu-link">{config.register_text}</Link>
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
        <div className="pure-u-5-24 centre-brand">
          <Link to="/" className="brand" onClick={this.resetDropdown}>
            {config.header_title}
          </Link>
        </div>
        <div className="pure-u-3-24"/>
        <div className="pure-u-8-24">
          <form className="pure-form search-form">
            <input
              type="text"
              name="query"
              className="search-rounded pure-input-3-4"
              placeholder={config.search_action}
              value={this.state.query}
              onChange={this.handleSearchInputChange}
              required={true}
            />
            <Link to={"/search/" + encodeURIComponent(this.state.query)}>
              <button
                type="submit"
                className="pure-button pure-button-primary search-button"
                onClick={this.handleSearchSubmit}
              >
                <Search />
              </button>
            </Link>
          </form>
        </div>
        <div className="pure-u-7-24">
          <div className="pure-menu pure-menu-horizontal">
            {Menu}
          </div>
        </div>
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
              {config.follow_text}
            </Link>
          </li>
          <li className="pure-menu-item">
            <Link to="/logout" className="pure-menu-link" onClick={this.resetDropdown}>
              {config.logout_text}
            </Link>
          </li>
        </ul>
      </li>
    );
    const Feed = (
        <li className="pure-menu-item">
          <Link to="/feed" className="pure-menu-link" onClick={this.resetDropdown}>
            {config.feed_text}
          </Link>
        </li>
    );
    const Write = (
      <li className="pure-menu-item">
        <Link to="/write" className="pure-menu-link" onClick={this.resetDropdown}>
          {config.write_text}
        </Link>
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

  private handleSearchInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      query: target.value,
    });
  }

  private handleSearchSubmit(event: React.MouseEvent<HTMLButtonElement>) {
    this.setState({
      query: "",
    });
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

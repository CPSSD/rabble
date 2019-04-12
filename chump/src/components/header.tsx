import * as React from "react";
import { Search } from "react-feather";
import { Link, Redirect, RouteComponentProps } from "react-router-dom";
import { withRouter } from "react-router";

import * as config from "../../rabble_config.json";

interface ILinkMap {
  [route: string]: string;
}

type IHeaderProps = RouteComponentProps & {
  username: string;
  userId: number;
  // navLinks is a list of tuples corresponding to the links to render
  // The tuple itself is: [Link Path, Link Name]
  navLinks: [string, string][];
}

interface IHeaderState {
  display: string;
  query: string;

  navLinks: [string, string][];
  linkMap: ILinkMap;
}

class Header extends React.Component<IHeaderProps, IHeaderState> {
  constructor(props: IHeaderProps) {
    super(props);

    const linkMap: ILinkMap = {}
    for (let i = 0; i < props.navLinks.length; i++) {
      linkMap[props.navLinks[i][0]] = props.navLinks[i][1];
    }

    this.state = {
      display: "none",
      query: "",
      navLinks: props.navLinks,
      linkMap: linkMap,
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
      <div className="topnav">
        <div className="pure-g">
          <div className="pure-u-1-24"/>
          <div className="pure-u-4-24 centre-brand">
            <Link to="/" className="brand" onClick={this.resetDropdown}>
              {config.header_title}
            </Link>
          </div>
          <div className="pure-u-9-24">
            <label
              htmlFor="header-search-bar"
              className="search-bar-icon"
            >
              <Search />
            </label>
            <form className="pure-form search-form" onSubmit={this.handleSearchSubmit}>
              <input
                id="header-search-bar"
                type="text"
                name="query"
                className="search-bar pure-input-1"
                placeholder={config.search_action}
                value={this.state.query}
                onChange={this.handleSearchInputChange}
                required={true}
              />
            </form>
          </div>
          <div className="pure-u-4-24"/>
          <div className="pure-u-4-24">
            <div className="pure-menu pure-menu-horizontal">
              {Menu}
            </div>
          </div>
        </div>
        {this.renderUnderNav()}
      </div>
    );
  }

  private renderUnderNav() {
    if (this.props.username === "") {
      return <div className="subnav-spacer"/>;
    }

    return (
      <div className="pure-g subnav subnav-spacer">
        <div className="pure-u-1-24"/>
        <div className="pure-u-16-24">
          <div className="pure-menu pure-menu-horizontal">
              <ul className="pure-menu-list">
                {this.renderNavLinks()}
              </ul>
          </div>
        </div>
        <div className="pure-u-6-24">
          <div className="pure-menu pure-menu-horizontal">
            <ul className="pure-menu-list">
              <li className="pure-menu-item">
                <Link to="/write" className="pure-menu-link">
                  {config.write_text}
                </Link>
              </li>
              <li className="pure-menu-item">
                <Link to="/follow" className="pure-menu-link">
                  {config.follow_text}
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  private renderMenu() {
    const UserMenu = (
      <li className="pure-menu-item pure-menu-has-children">
        <button onClick={this.toggleDropdown} className="button-link pure-menu-link">
          @{this.props.username}
        </button>
        <ul id="dropdown" className="menu-dropdown pure-menu-children" style={{display: this.state.display}}>
          <li className="pure-menu-item">
            <Link to={`/@${this.props.username}`} className="pure-menu-link" onClick={this.resetDropdown}>
              Profile
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

    return (
      <ul className="pure-menu-list home-menu">
        {UserMenu}
      </ul>
    );
  }

  private renderNavLinks() {
    var selected = "";
    if (this.state.linkMap.hasOwnProperty(this.props.location.pathname)) {
      selected = this.props.location.pathname;
    }

    return this.state.navLinks.map((navLink: [string, string], i: number) => {
      const link = navLink[0];
      const name = navLink[1];

      let classname = "nav-feed-link pure-menu-link ";
      if (link === selected) {
        classname = classname + " nav-feed-selected";
      }

      return (
        <li className="pure-menu-item" key={i}>
          <Link to={link} className={classname}>
            { name }
          </Link>
        </li>
      );
    });
  }

  private handleSearchInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      query: target.value,
    });
  }

  private handleSearchSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (this.state.query !== "") {
      this.props.history.push("/search/" + this.state.query);
    }
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

export const HeaderWithRouter = withRouter(Header);

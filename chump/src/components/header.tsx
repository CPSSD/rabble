import * as React from "react";
import { Plus, Search, UserPlus } from "react-feather";
import { withRouter } from "react-router";
import { Link, Redirect, RouteComponentProps } from "react-router-dom";

import * as config from "../../rabble_config.json";

interface ILinkMap {
  [route: string]: string;
}

type IHeaderProps = RouteComponentProps & {
  username: string;
  userId: number;
};

interface IHeaderState {
  display: string;
  query: string;
}

const navLinks: Array<[string, string]> = [
  ["/", config.all_nav],
  ["/feed", config.feed_nav],
  ["/recommended_posts", config.explore_nav],
];

const linkMap: ILinkMap = {};
for (const link of navLinks) {
  linkMap[link[0]] = link[1];
}

class Header extends React.Component<IHeaderProps, IHeaderState> {
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
    const Menu = this.renderMenu();

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
            <form
              className="pure-form search-form"
              onSubmit={this.handleSearchSubmit}
            >
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
          <div className="pure-u-3-24"/>
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
    const links = (
      <div className="pure-menu pure-menu-horizontal">
        <ul className="pure-menu-list">
          {this.renderNavLinks()}
        </ul>
      </div>
    );

    return (
      <div className="pure-g subnav subnav-spacer">
        <div className="pure-u-1-24"/>
        <div className="pure-u-6-24">
          {links}
        </div>
        <div className="pure-u-10-24"/>
        <div className="pure-u-6-24">
          <div className="pure-menu pure-menu-horizontal">
            {this.renderActions()}
          </div>
        </div>
      </div>
    );
  }

  private renderActions() {
    if (this.props.username === "") {
      return (
      <ul className="pure-menu-list">
        <li className="pure-menu-item">
          <Link to="/about" className="pure-menu-link nav-action">
            {config.about}
          </Link>
        </li>
      </ul>
      );
    }

    return (
      <ul className="pure-menu-list">
        <li className="pure-menu-item">
          <Link to="/write" className="pure-menu-link nav-action">
            <Plus size="1em"/> {config.write_text}
          </Link>
        </li>
        <li className="pure-menu-item">
          <Link to="/follow" className="pure-menu-link nav-action">
            <UserPlus size="1em"/> {config.follow_text}
          </Link>
        </li>
      </ul>
    );
  }

  private renderMenu() {
    if (this.props.username === "") {
      return (
        <ul className="pure-menu-list">
          <li className="pure-menu-item">
            <Link to="/login" className="pure-menu-link nav-action">
              {config.login_text}
            </Link>
          </li>
          <li className="pure-menu-item">
            <Link to="/register" className="pure-menu-link nav-action">
              {config.register_text}
            </Link>
          </li>
        </ul>
      );
    }

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
    let useLinks = navLinks;
    if (this.props.username === "") {
      useLinks = useLinks.slice(0, 1);
    }

    let selected = "";

    if (linkMap.hasOwnProperty(this.props.location.pathname)) {
      selected = this.props.location.pathname;
    }

    return useLinks.map((navLink: [string, string], i: number) => {
      const link = navLink[0];
      const name = navLink[1];

      let classname = "nav-feed-link pure-menu-link ";
      if (link === selected) {
        classname = classname + " nav-feed-selected";
      }

      return (
        <li className="pure-menu-item nav-feed-item" key={i}>
          <Link to={link} className={classname}>
            {name}
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

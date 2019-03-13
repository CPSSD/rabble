import * as React from "react";
import { ChevronDown, ChevronUp, Search } from "react-feather";
import { Link, RouteProps } from "react-router-dom";

import { IParsedPost } from "../models/posts";
import { IParsedUser, ISearchResponse, SearchRequest } from "../models/search";
import { Post } from "./post";
import { RootComponent } from "./root_component";
import { User } from "./user";

interface ISearchResultsProps extends RouteProps {
  match: {
    params: {
      query: string,
    },
  };
  username: string;
}

interface ISearchResultsState {
  foundPosts: IParsedPost[];
  foundUsers: IParsedUser[];
  query: string;
  display: string;
}

interface IExpandOrClose {
  display: string;
}

const SHOW_ITEM = "inherit";
const HIDE_ITEM = "none";

const ExpandOrClose: React.SFC<IExpandOrClose> = (props) => {
  // If User items are hidden show expand icon. Else show close
  if (props.display === HIDE_ITEM) {
    return (
        <div>
          More Users <ChevronDown size="1em"/>
        </div>
    );
  }
  return (
    <div>
      Close <ChevronUp size="1em"/>
    </div>
  );
};

export class SearchResults extends RootComponent<ISearchResultsProps, ISearchResultsState> {
  constructor(props: ISearchResultsProps) {
    super(props);
    this.state = {
      display: HIDE_ITEM,
      foundPosts: [],
      foundUsers: [],
      query: this.props.match.params.query,
    };

    this.toggleDropdown = this.toggleDropdown.bind(this);
    this.handleSearchInputChange = this.handleSearchInputChange.bind(this);
    this.handleSearchSubmit = this.handleSearchSubmit.bind(this);
  }

  public componentDidMount() {
    this.getResults(this.state.query);
  }

  public componentDidUpdate(prevProps: ISearchResultsProps) {
    if (prevProps.match.params.query !== this.props.match.params.query) {
      this.getResults(this.props.match.params.query);
    }
  }

  /* getResults is passed a query string so it can be called using
   * the state when using the on page search and a prop when the header
   * search is used.
   */
  public getResults(query: string) {
    SearchRequest(query)
      .then((resp: ISearchResponse) => {
        this.setState({
          foundPosts: resp.posts,
          foundUsers: resp.users,
          query,
        });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr() {
    this.alertUser("could not communicate with server :(");
  }

  public renderPosts() {
    if (this.state.foundPosts.length === 0) {
      return (
        <div className="pure-g pure-u-1">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p>No Posts found</p>
          </div>
        </div>
      );
    }
    return this.state.foundPosts.map((e: IParsedPost, i: number) => {
      return (
        <div className="pure-g pure-u-1" key={i}>
          <Post username={this.props.username} blogPost={e} preview={false} customCss={false}/>
        </div>
      );
    });
  }

  public renderUserSection() {
    if (this.state.foundUsers.length === 0) {
      return (
        <div className="pure-g pure-u-1">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p>No Users found</p>
          </div>
        </div>
      );
    }
    if (this.state.foundUsers.length === 1) {
      return (
        <div className="pure-g pure-u-1" key={this.state.foundPosts.length}>
          <User username={this.props.username} blogUser={this.state.foundUsers[0]} display={SHOW_ITEM}/>
        </div>
      );
    }
    const blogUsers = this.state.foundUsers.map((e: IParsedUser, i: number) => {
      if (i === 0) {
        return (
          <div className="pure-g pure-u-1" key={this.state.foundPosts.length + i}>
            <User username={this.props.username} blogUser={e} display={SHOW_ITEM}/>
          </div>
        );
      }
      return (
        <div className="pure-g pure-u-1" key={this.state.foundPosts.length + i}>
          <User username={this.props.username} blogUser={e} display={this.state.display}/>
        </div>
      );
    });

    blogUsers.push((
      <div className="pure-u-1" key={this.state.foundPosts.length + this.state.foundUsers.length}>
        <div className="pure-u-10-24"/>
        <button onClick={this.toggleDropdown} className="pure-button user-dropdown">
          <ExpandOrClose display={this.state.display} />
        </button>
      </div>
    ));
    return blogUsers;
  }

  public render() {
    const blogPosts = this.renderPosts();
    const userSection = this.renderUserSection();
    return (
      <div>
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <form className="pure-form full-search-form">
              <input
                type="text"
                name="query"
                className="search-rounded pure-input-3-4"
                placeholder="Search posts"
                value={this.state.query}
                onChange={this.handleSearchInputChange}
                required={true}
              />
              <button
                type="submit"
                className="pure-button pure-button-primary search-button"
                onClick={this.handleSearchSubmit}
              >
                <Search />
              </button>
            </form>
          </div>
        </div>
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <h3 className="search-divider">Users</h3>
          </div>
          {userSection}
        </div>
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <h3 className="search-divider">Posts</h3>
          </div>
          {blogPosts}
        </div>
      </div>
    );
  }

  private handleSearchInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      query: target.value,
    });
  }

  private handleSearchSubmit(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    this.getResults(this.state.query);
  }

  private toggleDropdown(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    let target = HIDE_ITEM;
    if (this.state.display === HIDE_ITEM) {
      target = SHOW_ITEM;
    }
    this.setState({
      display: target,
    });
  }
}

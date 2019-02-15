import * as React from "react";
import { ChevronDown, ChevronUp, Search } from "react-feather";
import { Link, RouteProps } from "react-router-dom";

import { IParsedPost } from "../models/posts";
import { IParsedUser, ISearchResponse, SearchRequest } from "../models/search";
import { Post } from "./post";
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

const showItem = "inherit";

const ExpandOrClose: React.SFC<IExpandOrClose> = (props) => {
  // If User items are hidden show expand icon. Else show close
  if (props.display === "none") {
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

export class SearchResults extends React.Component<ISearchResultsProps, ISearchResultsState> {
  constructor(props: ISearchResultsProps) {
    super(props);
    this.state = {
      display: "none",
      foundPosts: [],
      foundUsers: [],
      query: this.props.match.params.query,
    };

    this.toggleDropdown = this.toggleDropdown.bind(this);
    this.handleSearchInputChange = this.handleSearchInputChange.bind(this);
    this.handleSearchSubmit = this.handleSearchSubmit.bind(this);
  }

  public componentDidMount() {
    this.getResults("");
  }

  public componentDidUpdate(prevProps: ISearchResultsProps) {
    if (prevProps.match.params.query !== this.props.match.params.query) {
      this.getResults(this.props.match.params.query);
    }
  }

  public getResults(query: string) {
    let searchQuery = this.state.query;
    if (query !== "") {
      searchQuery = query;
    }
    SearchRequest(searchQuery)
      .then((resp: ISearchResponse) => {
        this.setState({
          foundPosts: resp.posts,
          foundUsers: resp.users,
          query: searchQuery,
        });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr() {
    alert("could not communicate with server :(");
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
          <Post username={this.props.username} blogPost={e} preview={false}/>
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
          <User username={this.props.username} blogUser={this.state.foundUsers[0]} display={showItem}/>
        </div>
      );
    }
    const blogUsers = this.state.foundUsers.map((e: IParsedUser, i: number) => {
      if (i === 0) {
        return (
          <div className="pure-g pure-u-1" key={this.state.foundPosts.length + i}>
            <User username={this.props.username} blogUser={e} display={showItem}/>
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
    this.getResults("");
  }

  private toggleDropdown(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    let target = "none";
    if (this.state.display === "none") {
      target = showItem;
    }
    this.setState({
      display: target,
    });
  }
}

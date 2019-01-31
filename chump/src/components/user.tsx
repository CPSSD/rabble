import * as React from "react";
import { Link, RouteProps } from "react-router-dom";

import { GetUsersPosts, IParsedPost } from "../models/posts";
import { Post } from "./post";

import * as superagent from "superagent";

interface IUserState {
  publicBlog: IParsedPost[];
  // user that we're looking at, filled when we complete our lookup
  user: string;
  // used to determine what error message to display.
  error: string;
}

interface IUserProps extends RouteProps {
  match: {
    params: {
      user: string,
    },
  };
  username: string;
}

export class User extends React.Component<IUserProps, IUserState> {
  constructor(props: IUserProps) {
    super(props);
    this.state = {
      error: "",
      publicBlog: [],
      user: "",
    };

    this.handleGetPostsErr = this.handleGetPostsErr.bind(this);
  }

  public getPosts() {
    GetUsersPosts(this.props.match.params.user)
      .then((posts: IParsedPost[]) => {
        this.setState({
          publicBlog: posts,
          user: this.props.match.params.user,
        });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr(e: superagent.ResponseError) {
    let msg: string = "";

    switch (e.status) {
      case 404:
        msg = "User not found.";
        break;
      case 401:
        msg = "Not allowed to access this user's feed.";
        break;
      default:
        const names = ["Ross'", "Noah's", "Cian's", "Aaron's"];
        const your = names[Math.floor(Math.random() * names.length)];
        msg = "An error occured, it was probably " + your + " fault.";
    }

    // We need to set user as well in the error handler because we use
    // it as a mechanism for detecting when we've already sent our first
    // request.
    this.setState({
      error: msg,
      user: this.props.match.params.user,
    });
  }

  public renderPosts() {
    if (this.props.match.params.user !== this.state.user) {
      this.getPosts();
    }

    if (this.state.publicBlog.length === 0) {
      let error = "No blogs here, yet!";
      if (this.state.error !== "") {
        error = this.state.error;
      }
      return (
        <div>
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p>{error}</p>
          </div>
        </div>
      );
    }
    return this.state.publicBlog.map((e: IParsedPost, i: number) => {
      return (
        <div className="pure-g" key={i}>
          <Post username={this.props.username} blogPost={e}/>
        </div>
      );
    });
  }

  public userLinks() {
    // TODO: Putting links here is a bit of a hack
    if (! (this.props.username === this.props.match.params.user)) {
      return false;
    }

    return (
      <div>
        <div className="pure-u-5-24"/>
        <div className="pure-u-10-24 user-menu">
          <Link to={"/@/edit"} className="pure-button">
            Edit account
          </Link>
          <Link to={"/@/pending"} className="pure-button">
            Follow requests
          </Link>
        </div>
      </div>
    );
  }

  public render() {
    // TODO: Make "Edit your account" button less ugly.
    const userEdit = this.userLinks();
    const blogPosts = this.renderPosts();
    return (
      <div>
        {userEdit}
        {blogPosts}
      </div>
    );
  }
}

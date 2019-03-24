import * as React from "react";
import { Link } from "react-router-dom";

import { GetUsersPosts, IAnyParsedPost, IParsedPost, IParsedSharedPost, IsSharedPost } from "../models/posts";
import { Post } from "./post";
import { SharedPost } from "./shared_post";

import * as superagent from "superagent";

interface IUserState {
  publicBlog: IAnyParsedPost[];
  ready: boolean;
  // used to determine what error message to display.
  error: string;
}

interface IUserProps {
  viewing: string;
  username: string;
}

export class User extends React.Component<IUserProps, IUserState> {
  constructor(props: IUserProps) {
    super(props);
    this.state = {
      error: "",
      publicBlog: [],
      ready: false,
    };

    this.handleGetPostsErr = this.handleGetPostsErr.bind(this);
  }

  public getPosts() {
    GetUsersPosts(this.props.viewing)
      .then((posts: IAnyParsedPost[]) => {
        this.setState({
          publicBlog: posts,
          ready: true,
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

    // We need to set ready as well in the error handler because we use
    // it as a mechanism for detecting when we've already sent our first
    // request.
    this.setState({
      error: msg,
      ready: true,
    });
  }

  public componentDidMount() {
    this.getPosts();
  }

  public renderPosts() {
    if (!this.state.ready) {
      return "Loading..";
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
    return this.state.publicBlog.map((e: IAnyParsedPost, i: number) => {
      if (IsSharedPost(e)) {
        return (
          <SharedPost
            username={this.props.username}
            blogPost={e as IParsedSharedPost}
            preview={false}
            customCss={true}
            key={i}
          />
        );
      }
      return (
        <div className="pure-g" key={i}>
          <Post
            username={this.props.username}
            blogPost={e}
            preview={false}
            customCss={true}
          />
        </div>
      );
    });
  }

  public render() {
    return (
      <div>
        {this.renderPosts()}
      </div>
    );
  }
}

import * as React from "react";
import { Link, RouteProps } from "react-router-dom";

import { GetUsersPosts, IParsedPost } from "../models/posts";
import { Post } from "./post";

interface IUserState {
  publicBlog: IParsedPost[];
  // user that we're looking at, filled when we complete our lookup
  user: string;
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
      publicBlog: [],
      user: "",
    };
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

  public handleGetPostsErr() {
    alert("could not communicate with server :(");
  }

  public renderPosts() {
    if (this.props.match.params.user !== this.state.user) {
      this.getPosts();
    }
    if (this.state.publicBlog.length === 0) {
      // TODO(CianLR): Detect which case this is and serve different messages.
      return (
        <div>
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p>User has no posts or does not exist</p>
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

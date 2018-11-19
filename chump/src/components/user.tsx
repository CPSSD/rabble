import * as React from "react";
import { Link, RouteProps } from "react-router-dom";

import { GetUsersPosts, IBlogPost } from "../models/posts";
import { Post } from "./post";

interface IUserState {
  publicBlog: IBlogPost[];
  user: string;
}

interface IUserProps extends RouteProps {
  match: {
    params: {
      user: string,
    },
  };
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
      .then((posts: IBlogPost[]) => {
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
    return this.state.publicBlog.map((e: IBlogPost, i: number) => {
      return (
        <div className="pure-g" key={i}>
          <Post username="" blogPost={e}/>
        </div>
      );
    });
  }

  public render() {
    const blogPosts = this.renderPosts();
    return (
      <div>
        {blogPosts}
      </div>
    );
  }
}

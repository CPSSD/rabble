import * as React from "react";
import { RouteProps } from "react-router-dom";

import { GetSinglePost, IBlogPost } from "../models/posts";
import { Post } from "./post";

interface ISinglePostState {
  posts: IBlogPost[];
  user: string;
}

interface ISinglePostProps extends RouteProps {
  match: {
    params: {
      user: string,
      article_id: string,
    },
  };
  username: string;
}

export class SinglePost extends React.Component<ISinglePostProps, ISinglePostState> {
  constructor(props: ISinglePostProps) {
    super(props);
    this.state = {
      posts: [],
      user: "",
    };
  }

  public componentDidMount() {
    GetSinglePost(this.props.match.params.user, this.props.match.params.article_id)
      .then((posts: IBlogPost[]) => {
        this.setState({
          posts,
          user: this.props.match.params.user,
        });
      })
      .catch(this.handleGetPostErr);
  }

  public handleGetPostErr() {
    alert("Could not communicate with server :(");
  }

  public renderPost() {
    if (this.state.posts.length === 0) {
      return (
        <div>
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p>404: Article not found</p>
          </div>
        </div>
      );
    }

    return (
      <div className="pure-g" key={1}>
        <Post username={this.props.username} blogPost={this.state.posts[0]}/>
      </div>
    );
  }

  public render() {
    const blogPost = this.renderPost();
    return (
      <div>
        {blogPost}
      </div>
    );
  }
}

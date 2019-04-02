import * as React from "react";
import { RouteProps } from "react-router-dom";

import { GetSinglePost, IParsedPost } from "../models/posts";
import { Post } from "./post";
import { RootComponent } from "./root_component";

interface ISinglePostState {
  posts: IParsedPost[];
}

interface ISinglePostProps extends RouteProps {
  match: {
    params: {
      article_id: string,
      user: string,
    },
  };
  username: string;
}

export class SinglePost extends RootComponent<ISinglePostProps, ISinglePostState> {
  constructor(props: ISinglePostProps) {
    super(props);
    this.state = {
      posts: [],
    };
  }

  public componentDidMount() {
    GetSinglePost(this.props.match.params.article_id)
      .then((posts: IParsedPost[]) => {
        this.setState({
          posts,
        });
      })
      .catch(this.handleGetPostErr);
  }

  public handleGetPostErr() {
    this.alertUser("Could not communicate with server :(");
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
        <Post
          username={this.props.username}
          blogPost={this.state.posts[0]}
          preview={false}
          customCss={true}
        />
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

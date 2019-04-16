import * as React from "react";
import { RouteProps } from "react-router-dom";

import { GetSinglePost, IParsedPost } from "../models/posts";
import { IParsedUser } from "../models/user";
import { Post } from "./post";
import { RootComponent } from "./root_component";
import { User } from "./user";

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
  history: {
    goBack: () => void;
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
      .catch(this.handleGeneralErr);
  }

  public renderPost() {
    if (this.state.posts.length === 0) {
      return (
        <div>
          <div className="pure-u-7-24"/>
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
          showBio={false}
          deleteSuccessCallback={this.props.history.goBack}
        />
      </div>
    );
  }

  public renderUserHeader() {
    if (this.state.posts.length === 0) {
      return null;
    }
    const user: IParsedUser = {
      bio: this.state.posts[0].bio,
      custom_css: "",  // Unused.
      display_name: this.state.posts[0].author_display,
      global_id: this.state.posts[0].author_id,
      handle: this.state.posts[0].author,
      host: this.state.posts[0].author_host,
      is_followed: this.state.posts[0].is_followed,
      private: {
        value: false,  // Unused.
      },
    };
    return (
      <User
        username={this.props.username}
        blogUser={user}
        display="inline"
      />
    );
  }

  public render() {
    const blogPost = this.renderPost();
    const userHeader = this.renderUserHeader();
    return (
      <div>
        {userHeader}
        {blogPost}
      </div>
    );
  }
}

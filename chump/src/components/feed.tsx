import * as React from "react";
import { Link } from "react-router-dom";

import { GetPublicPosts, IBlogPost } from "../models/posts";
import { Post } from "./post";

interface IFeedProps {
  username: string;
}

interface IFeedState {
  publicBlog: IBlogPost[];
}

export class Feed extends React.Component<IFeedProps, IFeedState> {
  constructor(props: IFeedProps) {
    super(props);
    this.state = { publicBlog: [] };
  }

  public componentDidMount() {
    this.getPosts();
  }

  public getPosts() {
    GetPublicPosts(this.props.username)
      .then((posts: IBlogPost[]) => {
        this.setState({ publicBlog: posts });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr() {
    alert("could not communicate with server :(");
  }

  public renderPosts() {
    return this.state.publicBlog.map((e: IBlogPost, i: number) => {
      return (
        <div className="pure-g" key={i}>
          <Post username={this.props.username} blogPost={e}/>
        </div>
      );
    });
  }

  public render() {
    const blogPosts = this.renderPosts();
    return (
      <div>
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <h3 className="article-title">Your blog post could be here!</h3>
            <p>Check out our <Link to="/about">about</Link> page for more info!</p>
          </div>
        </div>
        {blogPosts}
      </div>
    );
  }
}

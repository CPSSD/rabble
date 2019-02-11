import * as React from "react";
import { Link } from "react-router-dom";

import { GetPublicPosts, IParsedPost } from "../models/posts";
import { Post } from "./post";

const Config = require("Config");

interface IFeedProps {
  username: string;
  queryUsername: string;
}

interface IFeedState {
  publicBlog: IParsedPost[];
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
    GetPublicPosts(this.props.queryUsername)
      .then((posts: IParsedPost[]) => {
        this.setState({ publicBlog: posts });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr() {
    alert("could not communicate with server :(");
  }

  public renderPosts() {
    return this.state.publicBlog.map((e: IParsedPost, i: number) => {
      return (
        <div className="pure-g" key={i}>
          <Post username={this.props.username} blogPost={e} preview={false}/>
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
            <h3 className="article-title">{Config.feed_title}</h3>
            <p>Check out our <Link to="/about">about</Link> page for more info!</p>
          </div>
        </div>
        {blogPosts}
      </div>
    );
  }
}

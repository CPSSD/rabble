import * as React from "react";
import { Link } from "react-router-dom";

import { IAnyParsedPost } from "../models/posts";
import { Card } from "./card";
import { RootComponent } from "./root_component";

import * as config from "../../rabble_config.json";

interface IFeedBodyProps {
  username: string;
  queryUserId: number;
  feedTitle: string;
  GetPosts: (u: number) => any;
}

interface IFeedBodyState {
  publicBlog: IAnyParsedPost[];
}

export class FeedBody extends RootComponent<IFeedBodyProps, IFeedBodyState> {
  constructor(props: IFeedBodyProps) {
    super(props);
    this.state = { publicBlog: [] };
  }

  public componentDidMount() {
    this.getPosts();
  }

  public getPosts() {
    this.props.GetPosts(this.props.queryUserId)
      .then((posts: IAnyParsedPost[]) => {
        this.setState({ publicBlog: posts });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr() {
    this.alertUser("Could not communicate with server :(");
  }

  public renderPosts() {
    return this.state.publicBlog.map((e: IAnyParsedPost, i: number) => {
      return (
        <div className="pure-g" key={i}>
          <Card
            username={this.props.username}
            blogPost={e}
            customCss={false}
          />
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
            <h3 className="article-title">{this.props.feedTitle}</h3>
            <p>Check out our <Link to="/about">about</Link> page for more info!</p>
          </div>
        </div>
        {blogPosts}
      </div>
    );
  }
}

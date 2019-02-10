import * as React from "react";
import { Link, RouteProps } from "react-router-dom";

import { IParsedPost } from "../models/posts";
import { IParsedUser, ISearchResponse, Search } from "../models/search";
import { Post } from "./post";

interface IFeedProps extends RouteProps {
  match: {
    params: {
      query: string,
    },
  };
  username: string;
}

interface IFeedState {
  foundPosts: IParsedPost[];
  query: string;
}

export class SearchResults extends React.Component<IFeedProps, IFeedState> {
  constructor(props: IFeedProps) {
    super(props);
    this.state = {
      foundPosts: [],
      query: this.props.match.params.query,
    };
  }

  public componentDidMount() {
    this.getPosts();
  }

  public getPosts() {
    Search(this.state.query)
      .then((resp: ISearchResponse) => {
        this.setState({ foundPosts: resp.posts });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr() {
    alert("could not communicate with server :(");
  }

  public renderPosts() {
    return this.state.foundPosts.map((e: IParsedPost, i: number) => {
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
            <h3 className="article-title">Results found:</h3>
          </div>
        </div>
        {blogPosts}
      </div>
    );
  }
}

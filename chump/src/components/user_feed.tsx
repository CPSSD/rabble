import * as React from "react";
import { Link } from "react-router-dom";

import { GetUsersPosts, IAnyParsedPost  } from "../models/posts";
import { Card } from "./card";

import * as superagent from "superagent";
import * as config from "../../rabble_config.json";

interface IUserState {
  publicBlog: IAnyParsedPost[];
  ready: boolean;
  // used to determine what error message to display.
  error: string;
}

interface IUserProps {
  viewing: string;
  username: string;
  userId: number;
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

  public componentDidUpdate(prevProps: IUserProps) {
    if (prevProps.viewing !== this.props.viewing) {
      this.getPosts();
    }
  }

  public renderPosts() {
    if (!this.state.ready) {
      return (
        <div>
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p>{config.loading}</p>
          </div>
        </div>
      );
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
      return (
        <div className="pure-g" key={i}>
          <Card
            username={this.props.username}
            blogPost={e}
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

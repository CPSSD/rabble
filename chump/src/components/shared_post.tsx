import * as React from "react";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { SendLike } from "../models/like";
import { IParsedSharedPost } from "../models/posts";
import { Post } from "./post";
import { Reblog } from "./reblog_button";
import { RemoveProtocol } from "./util";

interface ISharedPostProps {
  blogPost: IParsedSharedPost;
  username: string;
  preview: boolean;
  customCss: boolean;
}

export class SharedPost extends React.Component<ISharedPostProps, {}> {
  constructor(props: ISharedPostProps) {
    super(props);
  }

  public render() {
    return (
      <div className="reblog-holder">

        <div className="pure-g">
          <div className="pure-u-5-24"/>
          {this.reblogText()}
        </div>

        <div className="pure-g">
          <Post
            username={this.props.username}
            blogPost={this.props.blogPost}
            preview={false}
            customCss={true}
            useSummary={true}
          />
        </div>
      </div>

    );
  }

  private reblogText() {
    let reblogger = this.props.blogPost.sharer;
    const host = this.props.blogPost.sharer_host;
    if (host !== null && host !== "" && typeof host !== "undefined") {
      reblogger = this.props.blogPost.sharer + "@" + RemoveProtocol(this.props.blogPost.sharer_host);
    }
    return (
      <div className="pure-u-10-24">
        <p className="reblog-line">
          Reblogged by {reblogger} &nbsp;
          {this.props.blogPost.parsed_share_date.toLocaleString()}
        </p>
      </div>
    );
  }

}

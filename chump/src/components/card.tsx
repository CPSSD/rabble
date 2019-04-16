import * as React from "react";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { IAnyParsedPost, IParsedSharedPost, IsSharedPost} from "../models/posts";
import { FollowButton} from "./follow_button";
import { RootComponent } from "./root_component";
import { Tags } from "./tags";
import { GenerateUserLinks, GetCustomCSS, RemoveProtocol } from "./util";

interface ICardProps {
  blogPost: IAnyParsedPost;
  username: string;
  customCss: boolean;
  showDivider: boolean;
}

const userLinksClassName = "username-holder";

export class Card extends RootComponent<ICardProps, {}> {
  constructor(props: ICardProps) {
    super(props);
    this.state = {};
    this.handleNoProfilePic = this.handleNoProfilePic.bind(this);
  }

  public render() {
    return (
      <div className="blog-post-holder">
        <div className="pure-u-5-24"/>
        {this.renderCard()}
        <div className="pure-u-1-24"/>
        {this.renderBio()}
      </div>
    );
  }

  private renderCard() {
    const post = this.props.blogPost;

    const customStyle = GetCustomCSS(post.author_id, this.props.customCss);

    let reblogLine: JSX.Element | boolean = false;
    if (IsSharedPost(this.props.blogPost)) {
      const rebloggedPost = post as IParsedSharedPost;
      let reblogger = "@" + rebloggedPost.sharer;
      const host = post.sharer_host;

      if (host !== null && host !== "" && typeof host !== "undefined") {
        reblogger = "@" + rebloggedPost.sharer + "@" + RemoveProtocol(rebloggedPost.sharer_host);
      }
      reblogLine = (
        <div>
          {`Reblogged by ${reblogger} at ${rebloggedPost.parsed_share_date.toLocaleString()}`}
        </div>
      );
    }

    let tags;
    if (typeof post.tags !== "undefined" && post.tags.length !== 0) {
      tags = (
        <div className="article-tags">
          <p>Tags:
            <Tags
              tags={post.tags}
              tagHolderClass="post-tag-holder"
              tagClass="post-tag"
            />
          </p>
        </div>
      );
    }

    return (
      <div className="pure-u-10-24">
        {this.props.showDivider ? <div className="article-divider" /> : null}
        {customStyle}
        <Link
          to={`/@${post.author}/${post.global_id}`}
          className="article-title"
        >
          {post.title}
        </Link>
        <p className="article-byline">
          {`${config.published} ${post.parsed_date.toLocaleString()}`}
          {reblogLine}
        </p>
        <p className="article-body">{post.summary}</p>
        <Link
          to={`/@${post.author}/${post.global_id}`}
          className="article-read-more"
        >
          {config.read_more_text}
        </Link>
        {tags}
      </div>
    );
  }

  private renderBio() {
    const userLink = GenerateUserLinks(this.props.blogPost.author,
      this.props.blogPost.author_host, this.props.blogPost.author_display,
      userLinksClassName);

    return (
      <div className="pure-u-3-24">
        {this.props.showDivider ? <div className="article-divider" /> : null}
        <div className="author-about">
          <img
            src={`/assets/user_${this.props.blogPost.author_id}`}
            onError={this.handleNoProfilePic}
            className="author-thumbnail"
          />
          <div style={{width: "100%"}}>
            {userLink}
          </div>
        </div>
      </div>
    );
  }

  private handleNoProfilePic(event: any) {
    event.target.onerror = null;
    event.target.src = this.props.blogPost.image;
  }
}

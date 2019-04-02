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
}

const userLinksClassName = "username-holder";

export class Card extends RootComponent<ICardProps, {}> {
  constructor(props: ICardProps) {
    super(props);
    this.state = {};
    this.handleNoProfilePic = this.handleNoProfilePic.bind(this);
  }

  public render() {
    let card;
    card = IsSharedPost(this.props.blogPost) ?
           this.renderSharedCard() : this.renderCard();

    return (
      <div className="blog-post-holder">
        <div className="pure-u-5-24"/>
        {card}
        <div className="pure-u-1-24"/>
        {this.renderBio()}
      </div>
    );
  }

  private renderSharedCard() {
    const post = this.props.blogPost as IParsedSharedPost;

    let reblogger = post.sharer;
    const host = post.sharer_host;

    if (host !== null && host !== "" && typeof host !== "undefined") {
      reblogger = post.sharer + "@" + RemoveProtocol(post.sharer_host);
    }

    return (
      <div className="reblog-holder">
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p className="reblog-line">
              Reblogged by {reblogger} &nbsp;
              {post.parsed_share_date.toLocaleString()}
            </p>
          </div>
        </div>
        {this.renderCard()}
      </div>
    );
  }

  private renderCard() {
    const post = this.props.blogPost;

    const customStyle = GetCustomCSS(post.author_id, this.props.customCss);

    let tags;
    if (typeof post.tags !== "undefined" && post.tags.length !== 0) {
      tags = (
        <div className="pure-g">
          <div className="pure-u-3-24" key={-1}>
            <p>Tags:</p>
          </div>
          <Tags
            tags={post.tags}
            tagHolderClass="pure-u-3-24 post-tag-holder"
            tagClass="post-tag"
          />
        </div>
      );
    }

    return (
      <div className="pure-u-10-24">
        {customStyle}
        <p className="article-byline">
          {config.published} &nbsp;
          {post.parsed_date.toLocaleString()}
        </p>
        <Link
          to={`/@${post.author}/${post.global_id}`}
          className="article-title"
        >
          {post.title}
        </Link>
        <p className="article-body">{post.summary}</p>
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
        <div className="author-about">
          <img
            src={`/assets/user_${this.props.blogPost.author_id}`}
            onError={this.handleNoProfilePic}
            className="author-thumbnail"
          />
          <div style={{width: "100%"}}>
            {userLink}
            <div style={{float: "right"}} >
                <FollowButton
                    follower={this.props.username}
                    followed={this.props.blogPost.author}
                    followed_host={this.props.blogPost.author_host}
                    following={this.props.blogPost.is_followed}
                />
            </div>
          </div>

          <div style={{clear: "both"}}>
            <p className="author-bio" style={{float: "left"}}>
              {this.props.blogPost.bio}
            </p>
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

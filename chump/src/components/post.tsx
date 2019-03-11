import * as React from "react";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { SendLike } from "../models/like";
import { IParsedPost } from "../models/posts";
import { FollowButton} from "./follow_button";
import { Reblog } from "./reblog_button";

interface IPostProps {
  blogPost: IParsedPost;
  username: string;
  preview: boolean;
  customCss: boolean;
}

interface IPostState {
  likesCount: number;
  isLiked: boolean;
}

export class Post extends React.Component<IPostProps, IPostState> {
  constructor(props: IPostProps) {
    super(props);
    if (this.props.blogPost.likes_count === undefined) {
      this.props.blogPost.likes_count = 0;
    }
    if (this.props.blogPost.is_liked === undefined) {
      this.props.blogPost.is_liked = false;
    }
    this.state = {
      isLiked: this.props.blogPost.is_liked,
      likesCount: this.props.blogPost.likes_count,
    };
    this.handleLike = this.handleLike.bind(this);
  }

  public render() {
    return (
      <div className="blog-post-holder">
        <div className="pure-u-5-24"/>
        {this.renderPost()}
        <div className="pure-u-1-24"/>
        {this.renderBio()}
      </div>
    );
  }

  private renderPost() {
    // Set custom CSS for user if enabled.
    const bodyStyle = this.props.customCss ? this.props.blogPost.body_css : undefined;
    const titleStyle = this.props.customCss ? this.props.blogPost.title_css : undefined;
    return (
      <div className="pure-u-10-24">
        <p className="article-byline">
          {config.published} &nbsp;
          {this.props.blogPost.parsed_date.toLocaleString()}
        </p>
        <Link
          to={`/@${this.props.blogPost.author}/${this.props.blogPost.global_id}`}
          className="article-title"
          style={titleStyle}
        >
          {this.props.blogPost.title}
        </Link>
        <p
          className="article-body"
          style={bodyStyle}
          dangerouslySetInnerHTML={{ __html: this.props.blogPost.body }}
        />

        <div>
          <Reblog
            username={this.props.username}
            initReblogged={false}
            display={(!this.nonInteractivePost()) && !this.viewerIsAuthor()}
            blogPost={this.props.blogPost}
          />
        </div>
      </div>
    );
  }

  private renderBio() {
    let LikeButton: JSX.Element | boolean = (
      <button
        className="pure-button pure-input-1-3 pure-button-primary primary-button"
        onClick={this.handleLike}
      >
      {this.state.isLiked ? "Unlike" : "Like"}
      </button>
    );

    if (this.nonInteractivePost()) {
      LikeButton = false;
    }

    return (
      <div className="pure-u-3-24">
        <div className="author-about">
          <img
            src={this.props.blogPost.image}
            className="author-thumbnail"
          />
          <div style={{width: "100%"}}>
              <div style={{float: "left"}} >
                  <Link to={`/@${this.props.blogPost.author}`} className="author-displayname">
                    {this.props.blogPost.author}
                  </Link><br/>
                  <Link to={`/@${this.props.blogPost.author}`} className="author-handle">
                    @{this.props.blogPost.author}
                  </Link>
              </div>
              <div style={{float: "right"}} >
                  <FollowButton
                      follower={this.props.username}
                      followed={this.props.blogPost.author}
                      following={this.props.blogPost.is_followed}
                  />
              </div>
          </div>

          <div style={{clear: "both"}}>
            <p className="author-bio" style={{float: "left"}}>
              {this.props.blogPost.bio}
            </p>
            <div style={{clear: "both", width: "100%"}}>
                <div style={{float: "left"}}>
                    <p> Likes: {this.state.likesCount} </p>
                </div>
                <div style={{float: "right"}}>
                    {LikeButton}
                </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  private viewerIsAuthor() {
    return this.props.username === this.props.blogPost.author;
  }

  private nonInteractivePost() {
    return this.props.username === "" ||
        typeof this.props.username === "undefined" ||
        this.props.preview === true;
  }

  private handleLike(event: React.MouseEvent<HTMLButtonElement>) {
    SendLike(this.props.blogPost.global_id, !this.state.isLiked)
      .then((res: any) => {
        const resp = res!.body;
        if (resp === null) {
          alert("Error parsing like: " + res);
          return;
        }
        // If isLiked is false then change it to true and increment like count
        // or vice versa.
        this.setState({
          isLiked: !this.state.isLiked,
          likesCount: this.state.likesCount + (this.state.isLiked ? -1 : 1),
        });
      })
      .catch((err: any) => {
        let message = err.message;
        if (err.response) {
          message = err.response.text;
        }
        alert(message);
      });
  }
}

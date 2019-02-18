import * as React from "react";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { SendLike } from "../models/like";
import { IParsedPost } from "../models/posts";
import { FollowButton} from "./follow_button";

interface IPostProps {
  blogPost: IParsedPost;
  username: string;
  preview: boolean;
  customCss: boolean;
}

interface IPostState {
  likesCount: number;
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
      likesCount: this.props.blogPost.likes_count,
    };
    this.handleLike = this.handleLike.bind(this);
    this.handleUnlike = this.handleUnlike.bind(this);
  }

  public render() {
    const likeHandler = this.props.blogPost.is_liked ? this.handleUnlike : this.handleLike;
    let LikeButton: JSX.Element | boolean = (
      <button
          className="pure-button pure-input-1-3 pure-button-primary primary-button"
          onClick={likeHandler}
      >
      {this.props.blogPost.is_liked ? "Unlike" : "Like"}
      </button>
    );
    if (this.props.username === "" ||
        typeof this.props.username === "undefined" ||
        this.props.preview === true) {
      LikeButton = false;
    }
    // Set custom CSS for user if enabled.
    let bodyStyle = this.props.customCss ? this.props.blogPost.body_css : undefined;
    let titleStyle = this.props.customCss ? this.props.blogPost.title_css : undefined;
    return (
      <div className="blog-post-holder">
        <div className="pure-u-5-24"/>
        <div className="pure-u-10-24">
          <p className="article-byline">{config.published} {this.props.blogPost.parsed_date.toLocaleString()}</p>
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
        </div>
        <div className="pure-u-1-24"/>
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
                <p className="author-bio">{this.props.blogPost.bio}</p>
                <div style={{width: "100%"}}>
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
      </div>
    );
  }

  private handleLike(event: React.MouseEvent<HTMLButtonElement>) {
    SendLike(this.props.blogPost.global_id)
      .then((res: any) => {
        const resp = res!.body;
        if (resp === null) {
          alert("Error parsing like: " + res);
          return;
        }
        this.setState({
          likesCount: this.state.likesCount + 1,
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

  private handleUnlike(event: React.MouseEvent<HTMLButtonElement>) {
    alert("Not implemented, give out likes more carefully.");
  }
}

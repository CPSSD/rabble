import * as React from "react";
import { Link } from "react-router-dom";

import { SendLike } from "../models/like";
import { IBlogPost } from "../models/posts";
import { FollowButton} from "./follow_button";

interface IPostProps {
  blogPost: IBlogPost;
  username: string;
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
    this.state = {
      likesCount: this.props.blogPost.likes_count,
    };
    this.handleLike = this.handleLike.bind(this);
  }

  public render() {
    let LikeButton : JSX.Element | boolean = <button
                    className="pure-button pure-input-1-3 pure-button-primary"
                    onClick={this.handleLike}>Like</button>;
    if (this.props.username === "" ||
        typeof this.props.username === "undefined") {
        LikeButton = false;
    }
    return (
      <div className="blog-post-holder">
        <div className="pure-u-5-24"/>
        <div className="pure-u-10-24">
          <p className="article-byline">Published 1st January 1970</p>
          <Link
            to={`/@${this.props.blogPost.author}/${this.props.blogPost.global_id}`}
            className="article-title"
          >
            {this.props.blogPost.title}
          </Link>
          <p className="article-body" dangerouslySetInnerHTML={{ __html: this.props.blogPost.body }}/>
        </div>
        <div className="pure-u-1-24"/>
        <div className="pure-u-3-24">
          <div className="author-about">
            <img
              src="https://qph.fs.quoracdn.net/main-qimg-8aff684700be1b8c47fa370b6ad9ca13.webp"
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
                    <FollowButton follower={this.props.username} followed={this.props.blogPost.author} />
                </div>
            </div>
            <div style={{clear: "both"}}>
                <p className="author-bio">Nowadays everybody wanna talk like they got something to say.
                But nothing comes out when they move their lips; just a bunch of gibberish.</p>
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
}

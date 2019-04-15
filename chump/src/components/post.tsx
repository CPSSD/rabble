import * as React from "react";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { SendLike } from "../models/like";
import { IParsedPost } from "../models/posts";
import { DeleteButton } from "./delete_button";
import { EditButton } from "./edit_button";
import { FollowButton} from "./follow_button";
import { Reblog } from "./reblog_button";
import { RootComponent } from "./root_component";
import { Tags } from "./tags";
import { GenerateUserLinks, GetCustomCSS, RemoveProtocol } from "./util";

interface IPostProps {
  blogPost: IParsedPost;
  username: string;
  preview: boolean;
  customCss: boolean;
  showBio: boolean;
  deleteSuccessCallback: () => void;
}

interface IPostState {
  likesCount: number;
  isLiked: boolean;
}

const userLinksClassName = "username-holder";

export class Post extends RootComponent<IPostProps, IPostState> {
  constructor(props: IPostProps) {
    super(props);
    this.state = {
      isLiked: this.props.blogPost.is_liked,
      likesCount: this.props.blogPost.likes_count,
    };
    this.handleLike = this.handleLike.bind(this);
    this.handleNoProfilePic = this.handleNoProfilePic.bind(this);
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
    const post = this.props.blogPost;
    const customStyle = GetCustomCSS(post.author_id, this.props.customCss);

    let tags;
    if (typeof(post.tags) !== "undefined" && post.tags.length !== 0) {
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
          {`${config.published} ${post.parsed_date.toLocaleString()}`}
        </p>
        <Link
          to={`/@${post.author}/${post.global_id}`}
          className="article-title"
        >
          {post.title}
        </Link>
        <p
          className="article-body"
          dangerouslySetInnerHTML={{ __html: post.body }}
        />

        <Reblog
          username={this.props.username}
          initReblogged={post.is_shared}
          sharesCount={post.shares_count}
          display={(!this.nonInteractivePost()) && !this.viewerIsAuthor()}
          blogPost={post}
        />
        <div className="pure-g">
          <EditButton
            username={this.props.username}
            display={this.viewerIsAuthor() && !this.nonInteractivePost()}
            blogPost={post}
          />
          <DeleteButton
            username={this.props.username}
            display={this.viewerIsAuthor() && !this.nonInteractivePost()}
            blogPost={post}
            successCallback={this.props.deleteSuccessCallback}
          />
        </div>
        {tags}
      </div>
    );
  }

  private renderBio() {
    if (!this.props.showBio) {
      return null;
    }
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

  private handleNoProfilePic(event: any) {
    event.target.onerror = null;
    event.target.src = this.props.blogPost.image;
  }

  private viewerIsAuthor() {
    return this.props.username === this.props.blogPost.author &&
      this.props.blogPost.author_host === "";
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
        if (res.status !== 200) {
          this.errorToast({ debug: "Error parsing like: " + res, statusCode: res.status });
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
        this.errorToast({ debug: message });
      });
  }
}

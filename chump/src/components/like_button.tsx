import * as React from "react";

import * as config from "../../rabble_config.json";
import { IParsedPost } from "../models/posts";
import { SendLike } from "../models/like";
import { RootComponent } from "./root_component";

interface ILikeButtonProps {
  initiallyLiked: boolean;
  display: boolean;
  postId: number;
  likesCount: number;
}

interface ILikeButtonState {
  isLiked: boolean;
  likesCount: number;
}

export class LikeButton extends RootComponent<ILikeButtonProps, ILikeButtonState> {
  constructor(props: ILikeButtonProps) {
    super(props);

    this.state = {
      isLiked: this.props.initiallyLiked,
      likesCount: this.props.likesCount,
    };

    this.handleClick = this.handleClick.bind(this);
    this.renderLikeButton = this.renderLikeButton.bind(this);
    this.renderUnlikeButton = this.renderUnlikeButton.bind(this);
  }

  private renderLikeButton() {
    return (
      <button
        className="pure-button pure-input-1-3 pure-button-primary primary-button"
        onClick={this.handleClick}
      >
        {this.state.likesCount} Like
      </button>
    );
  }

  private renderUnlikeButton() {
    return (
      <button
        className="pure-button pure-input-1-3 pure-button-primary primary-button"
        onClick={this.handleClick}
      >
        {this.state.likesCount} Unlike
      </button>
    );
  }

  private handleClick(event: React.MouseEvent<HTMLButtonElement>) {
    SendLike(this.props.postId, !this.state.isLiked)
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

  public render() {
    if (!this.props.display) {
      return null
    }
    if (this.state.isLiked) {
      return this.renderUnlikeButton();
    } else {
      return this.renderLikeButton();
    }
  }

}

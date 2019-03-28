import * as React from "react";
import { UserCheck, UserMinus, UserPlus } from "react-feather";
import { Link } from "react-router-dom";
import { Response } from "superagent";
import * as config from "../../rabble_config.json";
import { CreateFollow, Unfollow } from "../models/follow";
import { RootComponent } from "./root_component";

interface IFormState {
  following: boolean; // true if active user already follows the other user.
}

export interface IFormProps {
  follower: string;
  followed: string;
  followed_host: string;
  following: boolean;
}

interface IFollowOrUnfollowProps {
  following: boolean;
}

const FollowOrUnfollowButton: React.SFC<IFollowOrUnfollowProps> = (props) => {
  if (props.following) {
    /* We use CSS to hide and show the Feather icons and associated button text depending
       on the button :hover state (along with background colour, etc).*/
    return (
        <button
             type="submit"
             className="pure-button pure-button-primary primary-button follow-button unfollow"
        >
            <div className="following-button-content"><UserCheck size="1em" /> {config.following}</div>
            <div className="unfollow-button-content"><UserMinus size="1em" /> {config.unfollow}</div>
        </button>
    );
  }
  return (
    <button
        type="submit"
        className="pure-button pure-button-primary primary-button follow-button follow"
    >
        <div className="follow-button-content"><UserPlus size="1em" /> {config.follow_text}</div>
    </button>
  );
};

export class FollowButton extends RootComponent<IFormProps, IFormState> {
  constructor(props: IFormProps) {
    super(props);

    this.state = {
      following: props.following,
    };

    this.handleSubmitForm = this.handleSubmitForm.bind(this);
  }

  public render() {
    if (this.props.follower === "" ||
        typeof this.props.follower === "undefined" ||
        this.props.follower === this.props.followed) {
        return null;
    }
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group follow-button-container">
          <FollowOrUnfollowButton following={this.state.following} />
        </div>
      </form>
    );
  }

  private handleSubmitFormFollow(event: React.FormEvent<HTMLFormElement>) {
    const promise = CreateFollow(this.props.follower,
                                 this.props.followed,
                                 this.props.followed_host);
    promise.then((res: Response) => {
      // TODO: Check no error.
      this.setState({
        following: true,
      });
    })
    .catch((err: any) => {
      let status = err.message;
      let message = err.message;
      if (err.response) {
        status = err.response.status;
        message = err.response.text;
      }
      this.alertUser(message);
    });
  }

  private handleSubmitFormUnfollow(event: React.FormEvent<HTMLFormElement>) {
    const promise = Unfollow(this.props.follower,
                             this.props.followed,
                             this.props.followed_host);
    promise.then((res: Response) => {
      // TODO: Check no error.
      this.setState({
        following: false,
      });
    })
    .catch((err: any) => {
      let status = err.message;
      let message = err.message;
      if (err.response) {
        status = err.response.status;
        message = err.response.text;
      }
      this.alertUser(message);
    });
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (this.state.following) {
        this.handleSubmitFormUnfollow(event);
    } else {
        this.handleSubmitFormFollow(event);
    }
  }
}

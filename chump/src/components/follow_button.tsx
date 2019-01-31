import * as React from "react";
import { Link } from "react-router-dom";
import { Response } from "superagent";
import { CreateFollow } from "../models/follow";

interface IFormState {
  clicked: boolean;
  following: boolean; // true if active user already follows the other user.
}

export interface IFormProps {
  follower: string;
  followed: string;
  following: boolean;
}

export class FollowButton extends React.Component<IFormProps, IFormState> {
  constructor(props: IFormProps) {
    super(props);

    this.state = {
      clicked: false,
      following: props.following,
    };

    this.handleSubmitForm = this.handleSubmitForm.bind(this);
    this.alertUser = this.alertUser.bind(this);
  }

  public render() {
    if (this.props.follower === "" ||
        typeof this.props.follower === "undefined" ||
        this.props.follower === this.props.followed) {
        return null;
    }
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group">
          <input
            type="submit"
            value={this.state.following ? "Unfollow" : "TODO Follow"}
            className="pure-button pure-button-primary primary-button"
          />
        </div>
      </form>
    );
  }

  private alertUser(message: string) {
    alert(message);
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const promise = CreateFollow(this.props.follower,
                                 this.props.followed);
    promise.then((res: Response) => {
      let message = "Posted follow.";
      if (res.hasOwnProperty("text")) {
        message += " Response: " + res.text;
      }
      this.alertUser(message);
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
}

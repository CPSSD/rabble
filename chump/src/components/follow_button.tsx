import * as React from "react";
import { Link } from "react-router-dom";
import { CreateFollow } from "../models/follow";

interface IFormState {
  clicked: boolean;
}

export interface IFormProps {
  follower: string;
  followed: string;
}

export class FollowButton extends React.Component<IFormProps, IFormState> {
  constructor(props: IFormProps) {
    super(props);

    this.state = {
      clicked: false,
    };

    this.handleSubmitForm = this.handleSubmitForm.bind(this);
    this.alertUser = this.alertUser.bind(this);
  }

  public render() {
    alert("follower: " + this.props.follower);
    if (this.props.follower == "" || this.props.follower == this.props.followed) {
        return null;
    }
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group">
          <input
            type="submit"
            value="Follow"
            className="pure-input-1-2"
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
    promise.then((res: any) => {
      let message = "Posted follow with response: ";
      if (res.text) {
        message += res.text;
      }
      this.alertUser(message);
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

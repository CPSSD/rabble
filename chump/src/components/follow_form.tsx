import * as React from "react";
import { Link } from "react-router-dom";
import { CreateFollow } from "../models/follow";

interface IFormState {
  followedUsername: string;
}

export interface IFormProps {
  username: string;
}

export class FollowForm extends React.Component<IFormProps, IFormState> {
  constructor(props: IFormProps) {
    super(props);

    this.state = {
      followedUsername: "",
    };

    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSubmitForm = this.handleSubmitForm.bind(this);
    this.alertUser = this.alertUser.bind(this);
  }

  public render() {
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group">
          <input
            type="text"
            name="followedUsername"
            value={this.state.followedUsername}
            onChange={this.handleInputChange}
            className="pure-input-1-2 blog-input"
            placeholder="user[@instance.com]"
          />
        </div>
        <button
          type="submit"
          className="pure-button pure-input-1-3 pure-button-primary"
        >
          Follow
        </button>
      </form>
    );
  }

  private handleInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      followedUsername: target.value,
    });
  }

  private alertUser(message: string) {
    alert(message);
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const promise = CreateFollow(this.props.username,
                                 this.state.followedUsername);
    promise.then((res: any) => {
      let message = "Posted follow with response: ";
      if (res.text) {
        message += res.text;
      }
      this.alertUser(message);
      this.setState({
        followedUsername: "",
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

import * as React from "react";
import { Link } from "react-router-dom";
import * as config from "../../rabble_config.json";
import { CreateFollow, CreateRssFollow } from "../models/follow";
import { RootComponent } from "./root_component";

interface IFormState {
  toFollow: string;
  type: string;
}

export interface IFormProps {
  username: string;
  userId: number;
}

export class FollowForm extends RootComponent<IFormProps, IFormState> {
  constructor(props: IFormProps) {
    super(props);

    this.state = {
      toFollow: "",
      type: "username",
    };

    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleDropdownChange = this.handleDropdownChange.bind(this);
    this.handleSubmitForm = this.handleSubmitForm.bind(this);
  }

  public render() {
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group">
          <input
            type="text"
            name="toFollow"
            value={this.state.toFollow}
            onChange={this.handleInputChange}
            className="pure-input-1-2 blog-input"
            placeholder="user[@instance.com]"
          />
          <label>
            {config.type}: &nbsp;
            <select
              id="type"
              className="pure-input-4-5"
              onChange={this.handleDropdownChange}
              value={this.state.type}
            >
                <option value="username">{config.username}</option>
                <option value="url">Rss/Atom</option>
            </select>
          </label>
        </div>
        <button
          type="submit"
          className="pure-button pure-input-1-3 pure-button-primary primary-button"
        >
          {config.follow_text}
        </button>
      </form>
    );
  }

  private handleInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      toFollow: target.value,
    });
  }

  private handleDropdownChange(event: React.ChangeEvent<HTMLSelectElement>) {
    this.setState({
      type: event.target.value,
    });
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const promise = (this.state.type === "url")
      ? CreateRssFollow(this.props.username, this.state.toFollow)
      : CreateFollow(this.props.username, this.state.toFollow, "");

    promise.then((res: any) => {
      let message = "Posted follow with response: ";
      if (res.text) {
        message += res.text;
      }
      this.errorToast({ debug: message });
      this.setState({
        toFollow: "",
        type: "username",
      });
    })
    .catch((err: any) => {
      let status = err.message;
      let message = err.message;
      if (err.response) {
        status = err.response.status;
        message = err.response.text;
      }
      this.errorToast(message);
    });
  }
}

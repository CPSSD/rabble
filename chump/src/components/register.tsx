import * as React from "react";
import {Redirect, RouteProps} from "react-router-dom";
import * as config from "../../rabble_config.json";
import {GetRegisterPromise, IRegisterResult} from "../models/register";

interface IRegisterState {
  bio: string;
  displayName: string;
  username: string;
  password: string;
  redirect: boolean;
}

export class Register extends React.Component<RouteProps, IRegisterState> {
  constructor(props: RouteProps) {
    super(props);

    this.state = {
      bio: "",
      displayName: "",
      password: "",
      redirect: false,
      username: "",
    };

    this.handleUsername = this.handleUsername.bind(this);
    this.handlePassword = this.handlePassword.bind(this);
    this.handleBio = this.handleBio.bind(this);
    this.handleDisplayName = this.handleDisplayName.bind(this);
    this.handleRegister = this.handleRegister.bind(this);
  }

  public handleRegister(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (this.state.username === "" ||
        this.state.password === "" ||
        this.state.displayName === "") {
      return;
    }
    GetRegisterPromise(this.state.username,
                       this.state.password,
                       this.state.displayName,
                       this.state.bio)
      .then((response: IRegisterResult) => {
        if (!response.success) {
          alert("Error registering: " + response.error);
        } else {
          this.setState({
            redirect: true,
          });
        }
      })
      .catch(this.handleRegisterError);
  }

  public render() {
    if (this.state.redirect) {
      return <Redirect to={{ pathname: "/login" }}/>;
    }

    return (
      <div className="pure-g">
        <div className="pure-u-1-3"/>
        <div className="pure-u-3-5">
          <form className="pure-form pure-form-aligned" onSubmit={this.handleRegister}>
            <div className="pure-control-group">
              <input
                type="text"
                name="displayName"
                value={this.state.displayName}
                onChange={this.handleDisplayName}
                className="pure-input-1-2"
                placeholder={config.display_name}
              />
            </div>
            <div className="pure-control-group">
              <input
                type="text"
                name="username"
                value={this.state.username}
                onChange={this.handleUsername}
                className="pure-input-1-2"
                placeholder={config.username}
              />
            </div>
            <div className="pure-control-group">
              <input
                type="password"
                name="password"
                value={this.state.password}
                onChange={this.handlePassword}
                className="pure-input-1-2"
                placeholder={config.password}
              />
            </div>
            <div className="pure-control-group">
              <input
                type="text"
                name="bio"
                value={this.state.bio}
                onChange={this.handleBio}
                className="pure-input-1 blog-input"
                placeholder={config.bio_placeholder}
              />
            </div>
            <button
              type="submit"
              className="pure-button pure-input-1-3 pure-button-primary primary-button"
            >
              {config.register_text}
            </button>
          </form>
        </div>
      </div>
    );
  }

  private handleUsername(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      username: target.value,
    });
  }

  private handlePassword(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      password: target.value,
    });
  }

  private handleBio(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      bio: target.value,
    });
  }

  private handleDisplayName(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      displayName: target.value,
    });
  }

  private handleRegisterError() {
    alert("Error attempting to register.");
  }
}

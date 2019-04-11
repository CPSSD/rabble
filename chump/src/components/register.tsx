import * as React from "react";
import {Redirect, RouteProps} from "react-router-dom";
import * as config from "../../rabble_config.json";
import {GetRegisterPromise, IRegisterResult} from "../models/register";
import {RootComponent} from "./root_component";

interface IRegisterProps extends RouteProps {
  loginCallback(username: string, userId: number): void;
}

interface IRegisterState {
  bio: string;
  displayName: string;
  username: string;
  password: string;
  redirect: boolean;
}

export class Register extends RootComponent<IRegisterProps, IRegisterState> {
  constructor(props: IRegisterProps) {
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
        this.state.password === "") {
      this.errorToast({ message: "Username and Password are required" });
      return;
    }
    let displayName = this.state.displayName;
    if (displayName === "") {
      displayName = this.state.username;
    }
    GetRegisterPromise(this.state.username,
                       this.state.password,
                       displayName,
                       this.state.bio)
      .then((response: IRegisterResult) => {
        if (!response.success) {
          this.errorToast({debug: response.error});
        } else {
          this.props.loginCallback(this.state.username, response.user_id);
          this.setState({
            redirect: true,
          });
        }
      })
      .catch(this.handleGeneralErr);
  }

  public render() {
    if (this.state.redirect) {
      return <Redirect to={{ pathname: "/" }}/>;
    }

    return (
      <div className="pure-g">
        <div className="pure-u-1-5"/>
        <div className="pure-u-3-5">
          <form className="pure-form pure-form-aligned" onSubmit={this.handleRegister}>
            <div className="pure-control-group">
              <input
                type="text"
                name="displayName"
                value={this.state.displayName}
                onChange={this.handleDisplayName}
                className="pure-input-1-2"
                placeholder={config.display_name + " - " + config.defaults_to_username}
              />
            </div>
            <div className="pure-control-group">
              <input
                type="text"
                name="username"
                value={this.state.username}
                onChange={this.handleUsername}
                className="pure-input-1-2"
                placeholder={config.username + "*"}
                required={true}
              />
            </div>
            <div className="pure-control-group">
              <input
                type="password"
                name="password"
                value={this.state.password}
                onChange={this.handlePassword}
                className="pure-input-1-2"
                placeholder={config.password + "*"}
                required={true}
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
          <p>* = required</p>
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
}

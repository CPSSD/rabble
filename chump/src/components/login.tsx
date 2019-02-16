import * as React from "react";
import {Redirect, RouteProps} from "react-router-dom";
import * as config from "../../rabble_config.json";
import {GetLoginPromise, ILoginResult} from "../models/login";

interface ILoginProps extends RouteProps {
  loginCallback(username: string): void;
}

interface ILoginState {
  username: string;
  password: string;
  redirect: boolean;
}

export class Login extends React.Component<ILoginProps, ILoginState> {
  constructor(props: ILoginProps) {
    super(props);

    this.state = {
      password: "",
      redirect: false,
      username: "",
    };

    this.handleUsername = this.handleUsername.bind(this);
    this.handlePassword = this.handlePassword.bind(this);
    this.handleLogin = this.handleLogin.bind(this);
  }

  public handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (this.state.username === "" || this.state.password === "") {
      return;
    }
    GetLoginPromise(this.state.username, this.state.password)
      .then((response: ILoginResult) => {
        if (!response.success) {
          alert("Incorrect login!");
        } else {
          this.props.loginCallback(this.state.username);
          this.setState({
            redirect: true,
          });
        }
      })
      .catch(this.handleLoginError);
  }

  public render() {
    if (this.state.redirect) {
      // TODO: Add smarter redirect
      return <Redirect to={{ pathname: "/feed" }}/>;
    }

    return (
      <div className="pure-g">
        <div className="pure-u-1-3"/>
        <div className="pure-u-3-5">
          <form className="pure-form pure-form-aligned" onSubmit={this.handleLogin}>
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
            <button
              type="submit"
              className="pure-button pure-input-1-3 pure-button-primary primary-button"
            >
              {config.login_text}
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

  private handleLoginError() {
    alert("Error attempting to login.");
  }
}

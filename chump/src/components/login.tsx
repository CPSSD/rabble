import * as React from "react";
import {Redirect, RouteProps} from "react-router-dom";

interface ILoginProps extends RouteProps {
  loginCallback(username: string): void;
}

interface ILoginState {
  username: string;
  redirect: boolean;
}

export class Login extends React.Component<ILoginProps, ILoginState> {
  constructor(props: ILoginProps) {
    super(props);

    this.state = {
      redirect: false,
      username: "",
    };

    this.handleUsername = this.handleUsername.bind(this);
    this.handleLogin = this.handleLogin.bind(this);
  }

  public handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // TODO: Add authentication here
    if (this.state.username !== "") {
      this.props.loginCallback(this.state.username);
      this.setState({
        redirect: true,
      });
    }
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
                placeholder="Username"
              />
            </div>
            <button
              type="submit"
              className="pure-button pure-input-1-3 pure-button-primary"
            >
              Login
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
}

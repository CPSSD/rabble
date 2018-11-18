import * as Promise from "bluebird";
import * as React from "react";
import {Redirect, RouteProps} from "react-router-dom";
import * as superagent from "superagent";

interface ILogoutResult {
  success: boolean;
}

function GetLogoutPromise() {
  const url = "/c2s/logout";
  return new Promise<ILogoutResult>((resolve, reject) => {
    superagent
      .get(url)
      .set("Accept", "application/json")
      .end((error, res) => {
        if (error) {
          reject(error);
          return;
        }
        let succ = res!.body;
        if (succ === null) {
            succ = { success: false };
        }
        resolve(succ);
      });
  });
}

interface ILogoutProps extends RouteProps {
  logoutCallback(): void;
}

interface ILogoutState {
  redirect: boolean;
}

export class Logout extends React.Component<ILogoutProps, ILogoutState> {
  constructor(props: ILogoutProps) {
    super(props);

    this.state = {
      redirect: false,
    };

    this.componentDidMount = this.componentDidMount.bind(this);
    this.handleLogoutError = this.handleLogoutError.bind(this);
  }

  public componentDidMount() {
    GetLogoutPromise()
      .then((response: ILogoutResult) => {
        if (!response.success) {
          alert("Error logging out");
          return;
        }
        this.props.logoutCallback();
        this.setState({
          redirect: true,
        });
      })
      .catch(this.handleLogoutError);
  }

  public render() {
    if (this.state.redirect) {
      return <Redirect to={{ pathname: "/" }}/>;
    }

    return (
      <div className="pure-g">
        <div className="pure-u-1-3"/>
        <div className="pure-u-3-5">
        <p>Logging out...</p>
        </div>
      </div>
    );
  }

  private handleLogoutError(error: any) {
    alert("Error attempting to logout.");
    alert(error);
  }
}

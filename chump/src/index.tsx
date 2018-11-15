import * as React from "react";
import {render} from "react-dom";
import {Link, Route, HashRouter, Switch} from "react-router-dom";

import {PrivateRoute} from "./proute";
import {About} from "./components/about";
import {Header} from "./components/header";
import {Feed} from "./components/feed";
import {Write} from "./components/write";
import {Login} from "./components/login";

require("./styles/site.css"); // tslint:disable-line

// IAppState is top level state.
// Don't put state that might change often here.
interface IAppState {
  username: string
}

export class App extends React.Component<{}, IAppState> {
  constructor(props: {}) {
    super(props);

    this.state = {
      username: "",
    }

    this.login = this.login.bind(this);
  }

  login(username: string) {
    this.setState({username})
  }

  render() {
    return (
      <HashRouter>
        <div>
          <Header username={this.state.username} />
          <Switch>
            <Route
              exact={true}
              path="/"
              render={(props) => <Feed {...props} username=""/>}
            />
            <Route path="/about" component={About}/>
            <Route
              path="/login"
              render={(props) => <Login {...props} loginCallback={this.login} />}
            />
            <PrivateRoute
              path="/feed"
              username={this.state.username}
              component={Feed}
            />
            <PrivateRoute path="/write" username={this.state.username} component={Write}/>
          </Switch>
        </div>
      </HashRouter>
    );
  }
};

render(<App />, document.getElementById("root"));

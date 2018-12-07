import * as React from "react";
import {render} from "react-dom";
import {Link, Route, HashRouter, Switch} from "react-router-dom";

import {PrivateRoute} from "./proute";
import {About} from "./components/about";
import {Header} from "./components/header";
import {Feed} from "./components/feed";
import {Register} from "./components/register";
import {Write} from "./components/write";
import {Login} from "./components/login";
import {Logout} from "./components/logout";
import {User} from "./components/user";
import {Follow} from "./components/follow";
import {SinglePost} from "./components/single_post";
import {AccountEdit} from "./components/account_edit";
import {Pending} from "./components/pending";

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
    this.logout = this.logout.bind(this);
  }

  login(username: string) {
    this.setState({username})
  }

  logout() {
    this.setState({username: ""});
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
              path="/@/edit"
              component={AccountEdit}
            />
            <Route
              path="/@:user/:article_id"
              component={SinglePost}
            />
            <Route
              path="/@:user"
              render={(props) => <User {...props} username={this.state.username}/>}
            />
            <Route
              path="/login"
              render={(props) => <Login {...props} loginCallback={this.login} />}
            />
            <Route
              path="/logout"
              render={(props) => <Logout {...props} logoutCallback={this.logout} />}
            />
            <Route
              path="/register"
              component={Register}
            />
            <PrivateRoute
              path="/feed"
              username={this.state.username}
              component={Feed}
            />
            <PrivateRoute
              path="/follow"
              username={this.state.username}
              component={Follow}
            />
            <PrivateRoute
              path="/@/pending"
              username={this.state.username}
              component={Pending}
            />
            <PrivateRoute path="/write" username={this.state.username} component={Write}/>
          </Switch>
        </div>
      </HashRouter>
    );
  }
};

render(<App />, document.getElementById("root"));

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
import {User} from "./components/user_feed";
import {Follow} from "./components/follow";
import {SinglePost} from "./components/single_post";
import {AccountEdit} from "./components/account_edit";
import {Pending} from "./components/pending";
import {SearchResults} from "./components/search_results";

require("./styles/site.css"); // tslint:disable-line

// IAppState is top level state.
// Don't put state that might change often here.
interface IAppState {
  username: string
}

const LOCAL_STORAGE_USERNAME : string = "username";

export class App extends React.Component<{}, IAppState> {
  constructor(props: {}) {
    super(props);

    this.state = {
      username: this.getUsername(),
    }

    this.getUsername = this.getUsername.bind(this);
    this.login = this.login.bind(this);
    this.logout = this.logout.bind(this);
  }

  getUsername() : string {
    if (!localStorage.hasOwnProperty(LOCAL_STORAGE_USERNAME)) {
      return "";
    }
    return localStorage.getItem(LOCAL_STORAGE_USERNAME)!;
  }

  login(username: string) {
    this.setState({username});
    localStorage.setItem(LOCAL_STORAGE_USERNAME, username);
  }

  logout() {
    this.setState({username: ""});
    localStorage.removeItem(LOCAL_STORAGE_USERNAME);
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
              render={(props) => <Feed {...props} queryUsername="" username={this.state.username} />}
            />
            <Route path="/about" component={About}/>
            <Route
              path="/@:user/:article_id"
              render={(props) => <SinglePost {...props} username={this.state.username} />}
            />
            <Route
              path="/@:user"
              render={(props) => <User {...props} username={this.state.username} />}
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
            <Route
              path="/search/:query"
              username={this.state.username}
              component={SearchResults}
            />
            <PrivateRoute
              path="/feed"
              queryUsername={this.state.username}
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
            <PrivateRoute
              path="/@/edit"
              username={this.state.username}
              component={AccountEdit}
            />
            <PrivateRoute path="/write" username={this.state.username} component={Write}/>
          </Switch>
        </div>
      </HashRouter>
    );
  }
};

render(<App />, document.getElementById("root"));

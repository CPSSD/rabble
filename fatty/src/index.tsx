import * as React from "react";
import { render } from "react-dom";
import { HashRouter, Route, Switch } from 'react-router-dom';

import {Home} from './components/home';
import {About} from './components/about';
import {Header} from './components/header';

require("./styles/site.css");

const App = () => (
  <HashRouter>
    <div>
      <Header/>
      <Switch>
        <Route exact path="/" component={Home}/>
        <Route path="/about" component={About}/>
      </Switch>
    </div>
  </HashRouter>
);

render(<App />, document.getElementById("root"));

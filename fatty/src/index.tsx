import * as React from "react";
import { render } from "react-dom";
import { BrowserRouter, Route, Switch } from 'react-router-dom';

import {Home} from './components/home';
import {About} from './components/about';
import {Header} from './components/header';

const App = () => (
  <BrowserRouter>
	<div>
		<Header/>
		<Switch>
			<Route exact path="/" component={Home}/>
			<Route path="/about" component={About}/>
		</Switch>
	</div>
  </BrowserRouter>
);

render(<App />, document.getElementById("root"));

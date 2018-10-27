import * as React from "react";
import { Route,RouteProps, RouteComponentProps, Redirect } from "react-router-dom";

// PrivateRoute will not allow a user to see a route (see ReactRouter docs)
// Unless they're logged in. If anybody can figure out how to remove the any
// type that would be great.
export const PrivateRoute = ({ component, username, ...rest }: any) => {
  if (!component) {
    throw Error("component is undefined");
  }

  const Component = component;
  const render = (props: RouteComponentProps<any>): React.ReactNode => {
    if (username.length > 0) {
      return <Component {...props} />;
    }
    return <Redirect to={{ pathname: '/login' }} />
  };

  return (<Route {...rest} render={render} />);
}


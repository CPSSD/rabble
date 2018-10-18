import * as React from "react";
import { Link } from "react-router-dom";

export const Header: React.StatelessComponent<{}> = () => {
  return (
    <div className="pure-u-1 centre-brand">
      <Link to="/" className="brand">Rabble</Link>
    </div>
  );
};

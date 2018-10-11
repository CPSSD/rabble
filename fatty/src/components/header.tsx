import * as React from 'react';
import { Link } from 'react-router-dom';

export const Header: React.StatelessComponent<{}> = () => {
  return (
    <nav>
      <Link to="/">Rabble</Link>
      <Link to="/about">About</Link>
    </nav>
  );
}

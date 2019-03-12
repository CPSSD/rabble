import * as React from "react";

export class RootComponent<T, U> extends React.Component<T, U> {
  constructor(props: T) {
    super(props);
  }

  protected alertUser(message: string) {
    alert("got a message");
    alert(message);
  }
}

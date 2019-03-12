import * as React from "react";
import { SendLog } from "../models/log";

export class RootComponent<T, U> extends React.Component<T, U> {
  constructor(props: T) {
    super(props);
  }

  protected alertUser(message: string) {
    alert(message);
    SendLog(message);
  }
}

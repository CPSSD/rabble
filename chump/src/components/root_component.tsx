import * as React from "react";
import * as config from "../../rabble_config.json";
import { SendLog } from "../models/log";

export class RootComponent<T, U> extends React.Component<T, U> {
  constructor(props: T) {
    super(props);
  }

  protected alertUser(message: string) {
    alert(message);
    if (config.send_logs_to_server) {
      SendLog(message);
    }
  }
}

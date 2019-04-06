import * as React from "react";
import * as config from "../../rabble_config.json";
import { SendLog } from "../models/log";

interface IErrorToastArgs {
  message?: string;
  statusCode?: string;
  debug?: string;
}

export class RootComponent<T, U> extends React.Component<T, U> {
  constructor(props: T) {
    super(props);
  }

  protected errorToast(t: IErrorToastArgs) {
    if (t.debug) {
      console.log(t.debug);
    }

    if (t.statusCode) {
      // toast(genMessageFrom(statusCode))
      alert(t.statusCode);
    } else if (t.message !== "") {
      alert(t.message);
    } else {
      alert("An error occured");
    }

    if (config.send_logs_to_server) {
      SendLog(this.constructor.name + ": " + t.message);
    }
  }

  protected happyToast(message: string) {
    alert("happy " + message);
    if (config.send_logs_to_server) {
      SendLog(this.constructor.name + ": " + message);
    }
  }
}

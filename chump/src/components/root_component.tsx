import * as React from "react";
import { toast } from "react-toastify";

import * as config from "../../rabble_config.json";
import { SendLog } from "../models/log";

interface IErrorToastArgs {
  message?: string;
  statusCode?: number;
  debug?: any;
}

function genMessageFromStatus(code: number) {
  switch (code) {
    case 400: return config.bad_request;
    case 404: return config.not_found;
    case 418: return config.im_a_teapot;
    case 500: return config.something_went_wrong;
    default:  return config.something_went_wrong;
  }
}

export class RootComponent<T, U> extends React.Component<T, U> {
  constructor(props: T) {
    super(props);
  }

  // errorToast creates a toast notification with the given arguments.
  //
  // Arguments in an object (IErrorToastArgs) to make for a good API.
  //
  // If statusCode is passed, it will be prefereably rendered.
  // Otherwise, message is rendered. If no message is provided
  // we fall back to "Something went wrong" message.
  //
  // If a debug string is passed it will be logged to console.
  protected errorToast(t: IErrorToastArgs) {
    if (t.debug) {
      console.log("rabble debug: ", t.debug);
    }

    if (t.statusCode) {
      if (t.statusCode >= 200 && t.statusCode < 300) {
        console.log("Attempted to error with a 200ish response.");
        console.log(t);
        return;
      }
      toast.error(genMessageFromStatus(t.statusCode));
    } else if (t.message) {
      toast.error(t.message as string);
    } else {
      toast.error(config.something_went_wrong);
    }

    if (config.send_logs_to_server) {
      SendLog(this.constructor.name + ": " + t.message);
    }
  }

  // successToast creates a good toast notification with the given message.
  protected successToast(message: string) {
    toast.success(message);
  }
}

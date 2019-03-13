import * as React from "react";
import { Repeat } from "react-feather";

import * as config from "../../rabble_config.json";
import { IParsedPost } from "../models/posts";
import { SendReblog } from "../models/reblog";
import { RootComponent } from "./root_component";

interface IReblogProps {
  username: string;
  initReblogged: boolean;
  display: boolean;
  blogPost: IParsedPost;
}

interface IReblogState {
  isReblogged: boolean;
}

export class Reblog extends RootComponent<IReblogProps, IReblogState> {
  constructor(props: IReblogProps) {
    super(props);

    this.state = {
      isReblogged: this.props.initReblogged,
    };

    this.handleReblog = this.handleReblog.bind(this);
  }

  public render() {
    if (!this.props.display) {
      return null;
    }

    let inner = this.reblogInner;
    let handler = this.handleReblog;
    if (this.state.isReblogged) {
      inner = this.isRebloggedInner;
      handler = () => { // function is intentially left blank };
      };
    }

    return (
      <div onClick={handler}>
        {inner()}
      </div>
    );
  }

  private reblogInner() {
    return (
      <Repeat color="white" className="reblog-icon"/>
    );
  }

  private isRebloggedInner() {
    return (
      <Repeat color="white" className="reblog-icon-reblogged"/>
    );
  }

  private handleReblog() {
    SendReblog(this.props.blogPost.global_id)
      .then((res: any) => {
        this.setState({
          isReblogged: true,
        });
      })
      .catch((err: any) => {
        let message = err.message;
        if (err.response) {
          message = err.response.text;
        }
        this.alertUser(message);
      });
  }
}

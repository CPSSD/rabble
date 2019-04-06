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
  sharesCount: number;
}

interface IReblogState {
  isReblogged: boolean;
  sharesCount: number;
}

export class Reblog extends RootComponent<IReblogProps, IReblogState> {
  constructor(props: IReblogProps) {
    super(props);

    this.state = {
      isReblogged: this.props.initReblogged,
      sharesCount: this.props.sharesCount,
    };

    this.handleReblog = this.handleReblog.bind(this);
    this.renderButton = this.renderButton.bind(this);
  }

  public render() {
    let button = (<div/>);
    if (this.props.display) {
      button = this.renderButton();
    }

    return (
      <div>
        <div className="pure-u-5-24">
            <p className="shares-count"> Shares: {this.state.sharesCount} </p>
        </div>
        {button}
      </div>
    );
  }

  public renderButton() {
    let inner = this.reblogInner;
    let handler = this.handleReblog;
    if (this.state.isReblogged) {
      inner = this.isRebloggedInner;
      handler = () => { // function is intentially left blank };
      };
    }

    return (
      <div onClick={handler} className="pure-u-5-24">
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
          sharesCount: this.state.sharesCount + 1,
        });
      })
      .catch((err: any) => {
        let message = err.message;
        if (err.response) {
          message = err.response.text;
        }
        this.errorToast({ debug: message });
      });
  }
}

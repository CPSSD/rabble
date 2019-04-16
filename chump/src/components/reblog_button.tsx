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
    this.reblogInner = this.reblogInner.bind(this);
    this.isRebloggedInner = this.isRebloggedInner.bind(this);
    this.renderButton = this.renderButton.bind(this);
  }

  public render() {
    if (!this.props.display) {
      return null;
    }
    return this.renderButton();
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
      <button
        type="submit"
        className="pure-button pure-button-primary primary-button"
      >
        {this.state.sharesCount} <Repeat size="1em"/> Reblog
      </button>
    );
  }

  private isRebloggedInner() {
    return (
      <button
        type="submit"
        className="pure-button pure-button-primary primary-button"
        disabled={true}
      >
        {this.state.sharesCount} <Repeat size="1em"/> | Reblogged
      </button>
    );
  }

  private handleReblog() {
    SendReblog(this.props.blogPost.global_id)
      .then((res: Response) => {
        if (res.status !== 200) {
          this.errorToast({ statusCode: res.status });
          return;
        }
        this.successToast(config.reblog_success);
        this.setState({
          isReblogged: true,
          sharesCount: this.state.sharesCount + 1,
        });
      })
      .catch((err: Error) => {
        this.errorToast({ debug: err });
      });
  }
}

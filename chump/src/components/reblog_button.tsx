import * as React from "react";
import { Repeat } from "react-feather";

import * as config from "../../rabble_config.json";

interface IReblogProps {
  username: string;
  initReblogged: boolean;
  display: boolean;
}

interface IReblogState {
  isReblogged: boolean;
}

export class Reblog extends React.Component<IReblogProps, IReblogState> {
  constructor(props: IReblogProps) {
    super(props);

    this.state = { isReblogged: this.props.initReblogged };

    this.handleReblog = this.handleReblog.bind(this);
  }

  public render() {
    if (!this.props.display) {
      return null;
    }
    return (
      <div
          onClick={this.handleReblog}
      >
        {this.state.isReblogged ? this.isRebloggedInner() : this.reblogInner()}
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
    // TODO(devoxel): call skinny server here
    this.setState({
      isReblogged: true,
    });
  }
}

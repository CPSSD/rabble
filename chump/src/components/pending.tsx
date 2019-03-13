import * as React from "react";
import * as config from "../../rabble_config.json";
import { AcceptFollow, GetPendingFollows, IPendingFollow, IPendingFollows } from "../models/follow";
import { RootComponent } from "./root_component";

interface IPendingProps {
  username: string;
}

interface IPendingState {
  pending: IPendingFollows;
}

export class Pending extends RootComponent<IPendingProps, IPendingState> {
  constructor(props: IPendingProps) {
    super(props);

    this.state = {
      pending: { followers: [] },
    };
  }

  public componentDidMount() {
    this.getFollows();
  }

  public handleGetRequestsErr() {
    this.alertUser("Could not get follow requests.");
  }

  public handleAcceptErr() {
    this.alertUser("Could not accept follow request.");
  }

  public render() {
    return (
      <div>
        <div>
          <div className="pure-u-5-24"/>
          <div className="pure-u-14-24">
            <h2>{config.follow_requests}</h2>
          </div>
        </div>
        {this.renderFollowList()}
      </div>
    );
  }

  public renderFollowList() {
    return this.state.pending.followers!.map((e: IPendingFollow, i: number) => {
      let user = e.handle;
      if (e.hasOwnProperty("host")) {
        user = e.handle + "@" + e.host!.replace(/https?:\/\//g, "");
      }
      // We create a function on render
      // This slightly impacts performance, but it's negligible.
      const accept = () => this.acceptFollow(e, i, true);
      const deny = () => this.acceptFollow(e, i, false);
      return (
        <div className="pure-g follow-list" key={i}>
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            {user}
          </div>

          <div>
            <button
              type="submit"
              className="pure-button pure-button-primary primary-button"
              onClick={accept}
            >
              {config.accept}
            </button>
            <button
              type="submit"
              className="pure-button"
              onClick={deny}
            >
              {config.deny}
            </button>
          </div>

        </div>
      );
    });
  }

  private acceptFollow(follow: IPendingFollow, toDel: number, isAccepted: boolean) {
    AcceptFollow(this.props.username, follow, isAccepted)
      .then(() => {
        const followers = this.state.pending.followers!.filter(
          (_, i: number) => i !== toDel,
        );
        this.setState({
          pending: { followers },
        });
      })
      .catch(this.handleAcceptErr);
  }

  private getFollows() {
    GetPendingFollows()
      .then((follows: IPendingFollows) => {
        if (!follows.hasOwnProperty("followers")) {
          this.setState({ pending: { followers: [] }});
          return;
        }
        this.setState({ pending: follows });
      })
      .catch(this.handleGetRequestsErr);
  }
}

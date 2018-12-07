import * as React from "react";
import { AcceptFollow, GetPendingFollows, IPendingFollow, IPendingFollows } from "../models/follow";

interface IPendingProps {
  username: string;
}

interface IPendingState {
  pending: IPendingFollows;
}

export class Pending extends React.Component<IPendingProps, IPendingState> {
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
    alert("Could not get follow requests.");
  }

  public handleAcceptErr() {
    alert("Could not accept follow request.");
  }

  public render() {
    return (
      <div>
        <div>
          <div className="pure-u-5-24"/>
          <div className="pure-u-14-24">
            <h2>Follow Requests</h2>
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
        user = e.handle + "@" + e.host!.replace(/https?:\/\//g, '');
      }
      // We create a function on render
      // This slightly impacts performance, but it's negligible.
      const accept = () => this.acceptFollow(e, i);
      return (
        <div className="pure-g follow-list" key={i}>
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            {user}
          </div>

          <div>
            <button
              type="submit"
              className="pure-button  pure-button-primary"
              onClick={accept}
            >
              Accept
            </button>
          </div>

        </div>
      );
    });
  }

  private acceptFollow(follow: IPendingFollow, toDel: number) {
    AcceptFollow(this.props.username, follow)
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

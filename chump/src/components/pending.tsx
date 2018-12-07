import * as React from "react";
import { GetPendingFollows, IPendingFollow, IPendingFollows } from "../models/pending_follows";

interface IFeedState {
  pending: IPendingFollows;
}

export class Pending extends React.Component<{}, IFeedState> {
  constructor(props: any) {
    super(props);

    this.state = {
      pending: { followers: [] },
    };
  }

  public componentDidMount() {
    this.getFollows();
  }

  public handleGetPostsErr() {
    alert("Could not handle posts error");
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
    return this.state.pending.followers.map((e: IPendingFollow, i: number) => {
      let user = e.handle;
      if (e.host) {
        user = e.handle + "@" + e.host;
      }
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
            >
              Accept
            </button>
          </div>

        </div>
      );
    });
  }

  private getFollows() {
    GetPendingFollows()
      .then((follows: IPendingFollows) => {
        this.setState({ pending: follows });
      })
      .catch(this.handleGetPostsErr);
  }
}

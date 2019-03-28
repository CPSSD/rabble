import * as Promise from "bluebird";
import * as React from "react";

import { GetFollowers, GetFollowing, IFollowUser } from "../models/follow";
import { RootComponent } from "./root_component";

interface IFollowProps {
  username: string;
}

export class Followers extends RootComponent<IFollowProps, {}> {
  public render() {
    return (
      <FollowUserList
        username={this.props.username}
        headerText="Followers"
        queryList={GetFollowers}
      />
    );
  }
}

export class Following extends RootComponent<IFollowProps, {}> {
  public render() {
    return (
      <FollowUserList
        username={this.props.username}
        headerText="Following"
        queryList={GetFollowing}
      />
    );
  }
}

interface IFollowListProps {
  username: string;
  // headerText should reflect whether we are reading Following or Followers.
  headerText: string;
  queryList(username: string): Promise<IFollowUser[]>;
}

interface IFollowListState {
  ready: boolean;
  users: IFollowUser[];
}

class FollowUserList extends RootComponent<IFollowListProps, IFollowListState> {
  constructor(props: IFollowListProps) {
    super(props);
    this.state = {
      ready: false,
      users: [],
    };
  }

  public componentDidMount() {
    // Start request for getting followers
    this.props.queryList(this.props.username)
      .then((users: IFollowUser[]) => {
        this.setState({
          ready: true,
          users,
        });
      })
      .catch(this.handleQueryErr);
  }

  public renderFollowers() {
    return this.state.users.map((e: IFollowUser, i: number) => {
      let at = "";
      if (e.host !== undefined && e.host !== "") {
        at = "@" + e.host;
      }
      return (
        <div className="pure-u-5-5" key={i}>
          <p>{e.display_name} (@{e.handle}{at})</p>
        </div>
      );
    });
  }

  public render() {
    let list: JSX.Element[] | boolean = false;
    if (this.state.ready) {
      list = this.renderFollowers();
    }
    return (
      <div>
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-14-24">
            <h2> {this.props.headerText} </h2>
            {list}
          </div>
        </div>
      </div>
    );
  }

  private handleQueryErr() {
    this.alertUser("Failed to fetch " + this.props.headerText);
  }
}

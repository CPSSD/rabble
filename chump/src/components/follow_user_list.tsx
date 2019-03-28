import * as Promise from "bluebird";
import * as React from "react";

import * as config from "../../rabble_config.json";
import { GetFollowers, GetFollowing } from "../models/follow";
import { IParsedUser } from "../models/search";
import { RootComponent } from "./root_component";
import { User } from "./user";

interface IFollowProps {
  username: string;
}

export class Followers extends RootComponent<IFollowProps, {}> {
  public render() {
    return (
      <FollowUserList
        username={this.props.username}
        headerText={config.followers}
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
        headerText={config.following}
        queryList={GetFollowing}
      />
    );
  }
}

interface IFollowListProps {
  username: string;
  // headerText should reflect whether we are reading Following or Followers.
  headerText: string;
  queryList(username: string): Promise<IParsedUser[]>;
}

interface IFollowListState {
  ready: boolean;
  users: IParsedUser[];
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
      .then((users: IParsedUser[]) => {
        this.setState({
          ready: true,
          users,
        });
      })
      .catch(this.handleQueryErr);
  }

  public renderFollowers() {
    return this.state.users.map((e: IParsedUser, i: number) => {
      let at = "";
      if (e.host !== undefined && e.host !== "") {
        at = "@" + e.host;
      }
      return (
        <User
          key={i}
          username={this.props.username}
          blogUser={e}
          display="follow-user"
        />
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
          </div>
        </div>
        <div className="pure-g">
          {list}
        </div>
      </div>
    );
  }

  private handleQueryErr() {
    this.alertUser("Failed to fetch " + this.props.headerText);
  }
}

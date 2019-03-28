import * as React from "react";
import { Link, RouteProps } from "react-router-dom";

import { GetRecommendedFollows, IParsedUser, IRecommendedFollowsResponse } from "../models/recommended_follows";
import { User } from "./user";

interface IRecommendedFollowsProps extends RouteProps {
  username: string;
  userId: number;
}

interface IRecommendedFollowsState {
  recommendedFollows: IParsedUser[];
}

export class RecommendedFollows extends React.Component<IRecommendedFollowsProps, IRecommendedFollowsState> {
  constructor(props: IRecommendedFollowsProps) {
    super(props);
    this.state = {
      recommendedFollows: [],
    };
  }

  public componentDidMount() {
    this.getRecommendedFollows();
  }

  public getRecommendedFollows() {
    GetRecommendedFollows(this.props.userId)
      .then((resp: IRecommendedFollowsResponse) => {
        this.setState({
          recommendedFollows: resp.recommendedFollows,
        });
      })
      .catch(this.handleGetRecommendedFollowsError);
  }

  public handleGetRecommendedFollowsError() {
    alert("Could not communicate with server.");
  }

  public render() {
    if (this.state.recommendedFollows.length === 0) {
      return null;
    }
    const users = this.state.recommendedFollows.map((e: IParsedUser, i: number) => {
      return (
        <div className="pure-g pure-u-1" key={i}>
          <User
            username={this.props.username}
            blogUser={e}
            display="inherit"
            showFollowButton={true}
          />
        </div>
      );
    });

    return (
      <div>
        <div className="pure-g">
          <div className="pure-g pure-u-5-24"/>
          <div className="pure-g pure-u-10-24">
            Suggested users to follow based on your previous interactions:
          </div>
        </div>
        <br/>
        {users}
      </div>
    );
  }
}

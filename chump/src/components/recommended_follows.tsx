import * as React from "react";
import { Link, RouteProps } from "react-router-dom";

import { IParsedUser, GetRecommendedFollows, IRecommendedFollowsResponse } from "../models/recommended_follows";
import { User } from "./user";

interface IRecommendedFollowsProps extends RouteProps {
  username: string;
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
    GetRecommendedFollows(this.props.username)
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

  public renderRecommendedFollows() {
    if (this.state.recommendedFollows.length === 0) {
      return null;
    }
    const users = this.state.recommendedFollows.map((e: IParsedUser, i: number) => {
      return (
        <div className="pure-g pure-u-1" key={i}>
          <User username={this.props.username} blogUser={e} display="block" />
        </div>
      );
    });

    return users;
  }

  public render() {
    const recommendedFollows = this.renderRecommendedFollows();
    return (
      <div>
          {recommendedFollows}
      </div>
    );
  }
}

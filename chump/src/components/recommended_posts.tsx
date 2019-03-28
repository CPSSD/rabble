import * as React from "react";

import { GetRecommendedPosts } from "../models/recommended_posts";
import { FeedBody } from "./feed_body";
import { RootComponent } from "./root_component";

import * as config from "../../rabble_config.json";

interface IRecommendedPostsProps {
  username: string;
  queryUserId: number;
}

export class RecommendedPosts extends RootComponent<IRecommendedPostsProps, {}> {
  constructor(props: IRecommendedPostsProps) {
    super(props);
    this.state = { };
  }

  public render() {
    return (
      <FeedBody
        username={this.props.username}
        queryUserId={this.props.queryUserId}
        feedTitle={config.recommended_posts_title}
        GetPosts={GetRecommendedPosts}
      />
    );
  }
}

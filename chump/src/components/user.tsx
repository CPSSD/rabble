import * as React from "react";
import { Link } from "react-router-dom";

import { IParsedUser } from "../models/search";
import { FollowButton} from "./follow_button";

interface IUserProps {
  username: string;
  blogUser: IParsedUser;
  display: string;
}

interface IUserState {}

export class User extends React.Component<IUserProps, IUserState> {
  constructor(props: IUserProps) {
    super(props);
    this.state = {};
  }

  public render() {
    return (
      <div className="blog-post-holder" style={{display: this.props.display}}>
        <div className="pure-u-5-24"/>
        <div className="pure-u-14-24">
          <div className="pure-u-1-3">
            <img
              src={this.props.blogUser.image}
              className="author-thumbnail"
            />
          </div>
          <div className="pure-u-2-3">
            <div className="pure-u-1-3 username-holder">
                <Link to={`/@${this.props.blogUser.handle}`} className="author-displayname">
                  {this.props.blogUser.display_name}
                </Link>
                <Link to={`/@${this.props.blogUser.handle}`} className="author-handle">
                  @{this.props.blogUser.handle}
                </Link>
            </div>
            <div className="pure-u-1-3"/>
            <div className="pure-u-1-3 follow-holder">
                <FollowButton
                    follower={this.props.username}
                    followed={this.props.blogUser.handle}
                    following={this.props.blogUser.is_followed}
                />
            </div>
            <div className="pure-u-1">
                <p className="author-bio">{this.props.blogUser.bio}</p>
            </div>
          </div>
        </div>
        <div className="pure-u-5-24"/>
      </div>
    );
  }
}

import * as React from "react";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { IParsedUser } from "../models/search";
import { FollowButton} from "./follow_button";

interface IUserProps {
  username: string;
  blogUser: IParsedUser;
  display: string;
}

export class User extends React.Component<IUserProps, {}> {
  constructor(props: IUserProps) {
    super(props);
    this.state = {};
    this.handleNoProfilePic = this.handleNoProfilePic.bind(this);
  }

  public render() {
    let userLink = (
      <Link to={`/@${this.props.blogUser.handle}`} className="author-handle">
        @{this.props.blogUser.handle}
      </Link>
    );
    const host = this.props.blogUser.host;
    if (host !== null && host !== "" && typeof host !== "undefined") {
      userLink = (
        <Link to={`/@${this.props.blogUser.handle}`} className="author-handle">
          {this.props.blogUser.handle}@{host}
        </Link>
      );
    }
    return (
      <div className="blog-post-holder" style={{display: this.props.display}}>
        <div className="pure-u-5-24"/>
        <div className="pure-u-14-24">
          <div className="pure-u-5-24">
            <img
              src={`/assets/user_${this.props.blogUser.global_id}`}
              onError={this.handleNoProfilePic}
              className="author-thumbnail"
            />
          </div>
          <div className="pure-u-1-24"/>
          <div className="pure-u-18-24">
            <div className="pure-u-1-3 username-holder">
              <Link to={`/@${this.props.blogUser.handle}`} className="author-displayname">
                {this.props.blogUser.display_name}
              </Link>
              {userLink}
            </div>
            <div className="pure-u-1-3"/>
            <div className="pure-u-1-3 follow-holder">
                <FollowButton
                    follower={this.props.username}
                    followed={this.props.blogUser.handle}
                    followed_host={this.props.blogUser.host}
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

  private handleNoProfilePic(event: any) {
    event.target.onerror = null;
    event.target.src = this.props.blogUser.image;
  }
}

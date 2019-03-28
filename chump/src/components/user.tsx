import * as React from "react";
import { Link } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { IParsedUser } from "../models/search";
import { FollowButton} from "./follow_button";
import { GenerateUserLinks } from "./util";

interface IUserProps {
  username: string;
  blogUser: IParsedUser;
  display: string;
  showFollowButton: boolean;
}

const userLinksClassName = "pure-u-1-3 username-holder";

export class User extends React.Component<IUserProps, {}> {
  constructor(props: IUserProps) {
    super(props);
    this.state = {};
    this.handleNoProfilePic = this.handleNoProfilePic.bind(this);
  }

  public render() {
    const userLink = GenerateUserLinks(this.props.blogUser.handle,
      this.props.blogUser.host, this.props.blogUser.display_name,
      userLinksClassName);

    let followButton: JSX.Element | boolean = false;
    if (this.props.showFollowButton) {
      followButton = (
        <FollowButton
          follower={this.props.username}
          followed={this.props.blogUser.handle}
          followed_host={this.props.blogUser.host}
          following={this.props.blogUser.is_followed}
        />
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
            {userLink}
            <div className="pure-u-1-3"/>
            <div className="pure-u-1-3 follow-holder">
              {followButton}
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

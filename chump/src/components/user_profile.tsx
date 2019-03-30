import * as React from "react";

import { RouteProps } from "react-router-dom";
import * as config from "../../rabble_config.json";
import { AccountEdit } from "./account_edit";
import { Followers, Following } from "./follow_user_list";
import { Pending } from "./pending";
import { User } from "./user_feed";

/*
 * The profile page is where somebody lands if they click on a specific user.
 *
 * It has three seperate tabs, Posts, Followers, Following.
 * It also has some extra buttons if a viewer is viewing their own page.
 *
 * To simplify this user page we don't keep any state belonging to subcomponents here
 * This slightly impacts performance, because the REST endpoints are called
 * everytime you switch tab, but makes the code far cleaner and easier.
 *
 * The correct way to fix this would be to use redux, and allow that kind of state
 * to persist the life of Component state without clogging up the implementation.
 */

enum ViewingTab {
    Posts = 0,
    Following,
    Followers,
    UserSettings,
    FollowRequests,
}

const ViewingTabLookup = [
  config.posts,
  config.following,
  config.followers,
  config.settings,
  config.follow_requests,
];

interface IUserProfileState {
  viewing: ViewingTab;
  viewable: ViewingTab[];
  viewingUser: string;
}

interface IUserProfileProps extends RouteProps {
  match: {
    params: {
      user: string,
    },
  };
  userId: number;
  username: string;
}

export class UserProfile extends React.Component<IUserProfileProps, IUserProfileState> {
  constructor(props: IUserProfileProps) {
    super(props);

    this.state = {
      viewable: this.getViewable(),
      viewing: ViewingTab.Posts,
      viewingUser: this.props.match.params.user,
    };

    this.renderTab = this.renderTab.bind(this);
    this.getCurrentPage = this.getCurrentPage.bind(this);
    this.resetViewing = this.resetViewing.bind(this);
    this.renderTab = this.renderTab.bind(this);
    this.getViewable = this.getViewable.bind(this);
  }

  // getViewable returns the tabs that render on a given profile page.
  // If a user is viewing their own profile then they also see UserSettings
  // and FollowRequests.
  public getViewable() {
    let v = [ViewingTab.Posts, ViewingTab.Following, ViewingTab.Followers];
    if (this.isViewingOwnPage()) {
      v = v.concat([ViewingTab.UserSettings, ViewingTab.FollowRequests]);
    }
    return v;
  }

  public render() {
    const page = this.getCurrentPage();
    return (
      <div>
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-14-24">
            <div className="pure-menu pure-menu-horizontal">
                <ul className="profile-list pure-menu-list">
                  {this.state.viewable.map(this.renderTab)}
                </ul>
            </div>
          </div>
        </div>
        {page}
      </div>
    );
  }

  public componentDidUpdate(prevProps: IUserProfileProps) {
    if (this.props.match.params.user !== this.state.viewingUser) {
      this.setState({
        viewable: this.getViewable(),
        viewing: ViewingTab.Posts,
        viewingUser: this.props.match.params.user,
      });
    }
  }

  private resetViewing() {
    this.setState({viewing: ViewingTab.Posts});
  }

  private setViewing(e: ViewingTab) {
    return (event: React.MouseEvent<HTMLAnchorElement>) => {
      event.preventDefault();
      this.setState({viewing: e});
    };
  }

  private renderTab(e: ViewingTab, i: number) {
    let classname = "profile-item pure-menu-item";
    if (e === this.state.viewing) {
      classname = classname + " profile-selected pure-menu-selected";
    }

    return (
      <li className={classname} key={i}>
        <a
          onClick={this.setViewing(e)}
          className="profile-button pure-menu-link"
        >
          {ViewingTabLookup[e]}
        </a>
      </li>
    );
  }

  private getCurrentPage() {
    switch (this.state.viewing) {
      case ViewingTab.Posts:
        return (
          <User
            username={this.props.username}
            viewing={this.state.viewingUser}
            userId={this.props.userId}
          />
        );
      case ViewingTab.UserSettings:
        return (
          <AccountEdit
            username={this.props.username}
            resetCallback={this.resetViewing}
          />
        );
      case ViewingTab.FollowRequests:
        return <Pending username={this.props.username} />;
      case ViewingTab.Followers:
        return <Followers username={this.state.viewingUser} />;
      case ViewingTab.Following:
        return <Following username={this.state.viewingUser} />;
      default:
        return "You have bent the space time continuum to see this message.";
    }
  }

  private isViewingOwnPage() {
    const userMatch = this.props.match.params.user  === this.props.username;
    const validUsername = this.props.username !== "";
    // Ensure the user isn't viewing a page of a foriegn user.
    const noHost = !this.props.match.params.user.includes("@");
    return userMatch && validUsername && noHost;
  }

}

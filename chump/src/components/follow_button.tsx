import * as React from "react";
import { Link } from "react-router-dom";
import { Response } from "superagent";
import { CreateFollow } from "../models/follow";
import { UserPlus, UserCheck, UserMinus } from "react-feather";

interface IFormState {
  clicked: boolean;
  following: boolean; // true if active user already follows the other user.
}

export interface IFormProps {
  follower: string;
  followed: string;
  following: boolean;
}

interface IFollowOrUnfollowProps {
  following: boolean;
}

const FollowOrUnfollowButton: React.SFC<IFollowOrUnfollowProps> = (props) => {
  const iconStyle:React.CSSProperties = {
    float: "left",
    paddingRight: "0.5em"
  };
  if (props.following) {
    /* We use CSS to hide and show the Feather icons and associated button text depending
       on the button :hover state (along with background colour, etc).*/
    return (
        <button
             type="submit"
             className="pure-button pure-button-primary primary-button follow-button unfollow"
        >
            <div className="following-button-content"><UserCheck size="1em" style={iconStyle} /> Following</div>
            <div className="unfollow-button-content"><UserMinus size="1em" style={iconStyle} /> Unfollow</div>
        </button>
    );
  }
  return (
    <button
        type="submit"
        className="pure-button pure-button-primary primary-button follow-button follow"
    >
        <div className="follow-button-content"><UserPlus size="1em" style={iconStyle} /> Follow</div>
    </button>
  );
};

export class FollowButton extends React.Component<IFormProps, IFormState> {
  constructor(props: IFormProps) {
    super(props);

    this.state = {
      clicked: false,
      following: props.following,
    };

    this.handleSubmitForm = this.handleSubmitForm.bind(this);
    this.alertUser = this.alertUser.bind(this);
  }

  public render() {
    if (this.props.follower === "" ||
        typeof this.props.follower === "undefined" ||
        this.props.follower === this.props.followed) {
        return null;
    }
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group follow-button-container">
          <FollowOrUnfollowButton following={this.state.following} />
        </div>
      </form>
    );
  }

  private alertUser(message: string) {
    alert(message);
  }

  private handleSubmitFormFollow(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const promise = CreateFollow(this.props.follower,
                                 this.props.followed);
    promise.then((res: Response) => {
      let message = "Posted follow.";
      if (res.hasOwnProperty("text")) {
        message += " Response: " + res.text;
      }
      this.alertUser(message);
      // TODO: Check no error.
      this.setState({
        following: true,
      });
    })
    .catch((err: any) => {
      let status = err.message;
      let message = err.message;
      if (err.response) {
        status = err.response.status;
        message = err.response.text;
      }
      this.alertUser(message);
    });
  }

  private handleSubmitFormUnfollow(event: React.FormEvent<HTMLFormElement>) {
    this.alertUser("Woah there big fella! This cow hasn't gone to pasture yet.");
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    if (this.state.following) {
        this.handleSubmitFormUnfollow(event);
    } else {
        this.handleSubmitFormFollow(event);
    }
  }
}

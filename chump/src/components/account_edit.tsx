import * as React from "react";

import { Redirect } from "react-router-dom";
import {EditUserPromise, GetUserInfo, IEditUserResult, IUserDetails} from "../models/edit_user";

interface IAccountEditState {
  bio: string;
  currentPassword: string;
  displayName: string;
  newPassword: string;
  privateAccount: boolean;
  redirect: boolean;
}

interface IAccountEditProps {
  username: string;
}

export class AccountEdit extends React.Component<IAccountEditProps, IAccountEditState> {
  constructor(props: any) {
    super(props);

    this.state = {
      bio: "",
      currentPassword: "",
      displayName: "",
      newPassword: "",
      privateAccount: false,
      redirect: false,
    };

    this.handlePassword = this.handlePassword.bind(this);
    this.handleNewPassword = this.handleNewPassword.bind(this);
    this.handleBio = this.handleBio.bind(this);
    this.handleDisplayName = this.handleDisplayName.bind(this);
    this.handlePrivate = this.handlePrivate.bind(this);
    this.handleUpdate = this.handleUpdate.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleUserInfo = this.handleUserInfo.bind(this);
    this.handleGetError = this.handleGetError.bind(this);

    GetUserInfo().then(this.handleUserInfo).catch(this.handleGetError);
  }

  public render() {
    if (this.state.redirect) {
      return (<Redirect to={{ pathname: "/@" + this.props.username  }} />);
    }

    return (
      <div>
        <div className="pure-u-5-24"/>
        <div className="pure-u-14-24">
          <h2>Edit Your Profile</h2>
          {this.form()}
        </div>
      </div>
    );
  }

  public handleUpdate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    EditUserPromise(
      this.state.bio,
      this.state.displayName,
      this.state.currentPassword,
      this.state.newPassword,
      this.state.privateAccount,
    ).then((response: IEditUserResult) => {
      if (!response.success) {
        alert("Error editing: " + response.error);
      } else {
        this.setState({ redirect: true });
      }
    })
    .catch(this.handleUpdateError);
  }

  public handleUserInfo(details: IUserDetails) {
    let isPrivate = false;
    if ("value" in details.private) {
      isPrivate = details.private.value!;
    }

    this.setState({
      bio: details.bio,
      displayName: details.display_name,
      privateAccount: isPrivate,
    });
  }

  private form() {
    return (
      <div>
        <form
          className="pure-form pure-form-aligned"
          onSubmit={this.handleUpdate}
        >
          <fieldset>
            <legend>Blank fields are left unchanged</legend>
            <div className="pure-control-group">
                <label htmlFor="newPassword">New Password</label>
                <input
                  id="newPassword"
                  type="password"
                  placeholder="New Password"
                  className="pure-input-2-3"
                  value={this.state.newPassword}
                  onChange={this.handleNewPassword}
                />
            </div>
            <div className="pure-control-group">
                <label htmlFor="name">Display Name</label>
                <input
                  id="diplay_name"
                  type="text"
                  placeholder="Display Name"
                  className="pure-input-2-3"
                  value={this.state.displayName}
                  onChange={this.handleDisplayName}
                />
            </div>
            <div className="pure-control-group">
                <label htmlFor="name">Bio</label>
                <textarea
                  id="bio"
                  placeholder="Bio"
                  className="pure-input-2-3 bio-form"
                  value={this.state.bio}
                  onChange={this.handleBio}
                />
            </div>

            <div className="pure-control-group">
              <label htmlFor="private">Private Account</label>
              <input
                id="private"
                type="checkbox"
                checked={this.state.privateAccount}
                onChange={this.handlePrivate}
              />
            </div>

            <legend>Enter your current user account</legend>
            <div className="pure-control-group">
                <label htmlFor="name">Password</label>
                <input
                  id="password"
                  type="password"
                  placeholder="Password"
                  className="pure-input-2-3"
                  required={true}
                  value={this.state.currentPassword}
                  onChange={this.handlePassword}
                />
            </div>

            <div className="pure-control-group">
              <label/>
              <div className="edit-wrapper">
                <button
                  onClick={this.handleCancel}
                  className="pure-button cancel-button edit-button"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="pure-button pure-button-primary primary-button edit-button"
                >
                  Update!
                </button>
              </div>
            </div>
          </fieldset>
        </form>
      </div>
    );
  }

  private handleCancel(event: React.FormEvent<HTMLButtonElement>) {
    event.preventDefault();
    this.setState({ redirect: true });
  }

  private handleNewPassword(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      newPassword: target.value,
    });
  }

  private handlePassword(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      currentPassword: target.value,
    });
  }

  private handleBio(event: React.ChangeEvent<HTMLTextAreaElement>) {
    const target = event.target;
    this.setState({
      bio: target.value,
    });
  }

  private handlePrivate(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;

    this.setState({
      privateAccount: target.checked,
    });
  }

  private handleDisplayName(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      displayName: target.value,
    });
  }

  private handleUpdateError(e: any) {
    alert("Error attempting to update.", e);
  }

  private handleGetError(e: any) {
    alert("Error getting user details: ", e);
  }
}

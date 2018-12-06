import * as React from "react";

import {EditUserPromise, IEditUserResult} from "../models/edit_user";

interface IAccountEditState {
  bio: string;
  displayName: string;
  currentPassword: string;
  newPassword: string;
}

export class AccountEdit extends React.Component<{}, IAccountEditState> {

  constructor(props: any) {
    super(props);

    this.state = {
      bio: "",
      currentPassword: "",
      displayName: "",
      newPassword: "",
    };

    this.handlePassword = this.handlePassword.bind(this);
    this.handleNewPassword = this.handleNewPassword.bind(this);
    this.handleBio = this.handleBio.bind(this);
    this.handleDisplayName = this.handleDisplayName.bind(this);
    this.handleUpdate = this.handleUpdate.bind(this);
  }

  public render() {
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
    EditUserPromise(this.state.bio,
                    this.state.displayName,
                    this.state.currentPassword,
                    this.state.newPassword,
    ).then((response: IEditUserResult) => {
      if (!response.success) {
        alert("Error editing: " + response.error);
      }
    })
    .catch(this.handleUpdateError);
  }

  private form() {
    // TODO: It would be nice to fill in the current user details here
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

            <button
              type="submit"
              className="pure-button pure-input-2-3 pure-button-primary"
            >
              Update!
            </button>

          </fieldset>
        </form>
      </div>
    );
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

  private handleDisplayName(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      displayName: target.value,
    });
  }

  private handleUpdateError() {
    alert("Error attempting to update.");
  }
}

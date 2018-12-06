import * as React from "react";

interface IAccountEditState {
  bio: string;
  display_name: string;
  current_password: string;
  new_password: string;
}

export class AccountEdit extends React.Component<{}, IAccountEditState> {

  constructor(props: any) {
    super(props);

    this.state = {
      bio: "",
      display_name: "",
      current_password: "",
      new_password: "",
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
    console.log(this.state);
  }

  private form() {
    // TODO: It would be nice to fill in the current user details here
    return (
      <div>
        <form className="pure-form pure-form-aligned" onSubmit={this.handleUpdate}>
          <fieldset>
            <legend>Blank fields are left unchanged</legend>
            <div className="pure-control-group">
                <label htmlFor="new_password">New Password</label>
                <input
                  id="new_password"
                  type="password"
                  placeholder="New Password"
                  className="pure-input-2-3"
                  value={this.state.new_password}
                  onChange={this.handlePassword}
                />
            </div>
            <div className="pure-control-group">
                <label htmlFor="name">Display Name</label>
                <input
                  id="diplay_name"
                  type="text"
                  placeholder="Display Name"
                  className="pure-input-2-3"
                  value={this.state.display_name}
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
                  value={this.state.current_password}
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
      new_password: target.value,
    });
  }

  private handlePassword(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;
    this.setState({
      current_password: target.value,
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
      display_name: target.value,
    });
  }

}

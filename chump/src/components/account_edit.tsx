import * as React from "react";

export class AccountEdit extends React.Component<{}, {}> {

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

  private form() {
    // TODO: It would be nice to fill in the current user details here
    return (
      <div>
        <form className="pure-form pure-form-aligned">
          <fieldset>
            <legend>Blank fields are left unchanged</legend>
            <div className="pure-control-group">
                <label htmlFor="new_password">New Password</label>
                <input
                  id="new_password"
                  type="password"
                  placeholder="New Password"
                  className="pure-input-2-3"
                />
            </div>
            <div className="pure-control-group">
                <label htmlFor="name">Display Name</label>
                <input
                  id="diplay_name"
                  type="text"
                  placeholder="Display Name"
                  className="pure-input-2-3"
                />
            </div>
            <div className="pure-control-group">
                <label htmlFor="name">Bio</label>
                <textarea
                  id="bio"
                  placeholder="Bio"
                  className="pure-input-2-3 bio-form"
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
                />
            </div>
          </fieldset>
        </form>
      </div>
    );
  }
}

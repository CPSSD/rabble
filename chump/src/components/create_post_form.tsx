import * as React from "react";
import { Link } from "react-router-dom";

interface ICreatePostFormState {
  username: string;
  title: string;
  blogText: string;
}

class CreatePostForm extends React.Component<{}, ICreatePostFormState> {
  constructor(props: {}) {
    super(props);

    this.state = {
      blogText: "",
      title: "",
      username: "",
    };

    this.handleUsernameInputChange = this.handleUsernameInputChange.bind(this);
    this.handleTitleInputChange = this.handleTitleInputChange.bind(this);
    this.handleTextAreaChange = this.handleTextAreaChange.bind(this);
    this.handleSubmitForm = this.handleSubmitForm.bind(this);
  }

  public render() {
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group">
          <input
            type="text"
            name="username"
            value={this.state.username}
            onChange={this.handleUsernameInputChange}
            className="pure-input-1-2"
            placeholder="Username"
          />
        </div>
        <div className="pure-control-group">
          <input
            type="text"
            name="title"
            value={this.state.title}
            onChange={this.handleTitleInputChange}
            className="pure-input-1-2"
            placeholder="Title"
          />
          <textarea
            name="blogText"
            value={this.state.blogText}
            onChange={this.handleTextAreaChange}
            className="pure-input-1 blog-input"
            placeholder="Start here"
          />
        </div>
        <button
          type="submit"
          className="pure-button pure-input-1-3 pure-button-primary"
        >
          Post
        </button>
      </form>
    );
  }

  private handleUsernameInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;

    this.setState({
      username: target.value,
    });
  }

  private handleTitleInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;

    this.setState({
      title: target.value,
    });
  }

  private handleTextAreaChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    const target = event.target;

    this.setState({
      blogText: target.value,
    });
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    alert("Posted created");

    this.setState({
      blogText: "",
      title: "",
      username: "",
    });
  }
}

export default CreatePostForm;

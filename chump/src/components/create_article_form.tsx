import * as React from "react";
import { Link } from "react-router-dom";
import { CreateArticle } from "../models/article";

interface ICreateArticleFormState {
  username: string;
  title: string;
  blogText: string;
}

class CreateArticleForm extends React.Component<{}, ICreateArticleFormState> {
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
    this.alertUser = this.alertUser.bind(this);
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

  private alertUser(message: string) {
    alert(message);
  }

  private handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const promise = CreateArticle(this.state.username, this.state.title, this.state.blogText);
    promise
    .then((res: any) => {
      let message = "Posted article";
      if (res.text) {
        message = res.text;
      }
      this.alertUser(message);
      this.setState({
        blogText: "",
        title: "",
        username: "",
      });
    })
    .catch((err: any) => {
      let status = err.message;
      if (err.response) {
        status = err.response.status;
      }
      if (status === 403 || status === "403") {
        this.alertUser("You do not have permission to create a post under this username.");
      } else if (status === 400 || status === "400") {
        this.alertUser("Bad request");
      } else {
        this.alertUser("Something went wrong, Please try again.");
      }
    });
  }
}

export default CreateArticleForm;

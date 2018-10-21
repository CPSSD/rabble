import * as React from "react";
import { Link } from "react-router-dom";

interface CreatePostFormProps { }

interface CreatePostFormState {
  username: string,
  title: string,
  blogText: string
}

class CreatePostForm extends React.Component<CreatePostFormProps, CreatePostFormState> {
  constructor(props: CreatePostFormProps) {
    super(props)

    this.state = {
      username: "",
      title: "",
      blogText: ""
    };

    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleTextAreaChange = this.handleTextAreaChange.bind(this);
    this.handleSubmitForm = this.handleSubmitForm.bind(this);
  }

  handleInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const target = event.target;

    this.setState({
      [target.name]: target.value
    } as any);
  }

  handleTextAreaChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    const target = event.target;

    this.setState({
      [target.name]: target.value
    } as any);
  }

  handleSubmitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    alert("Posted created");


    this.setState({
      "username":"",
      "title":"",
      "blogText": ""
    })
  }

  render() {
    return (
      <form className="pure-form pure-form-aligned" onSubmit={this.handleSubmitForm}>
        <div className="pure-control-group">
          <input
            type="text"
            name="username"
            value={this.state.username}
            onChange={this.handleInputChange}
            className="pure-input-1-2"
            placeholder="Username" />
        </div>
        <div className="pure-control-group">
          <input
            type="text"
            name="title"
            value={this.state.title}
            onChange={this.handleInputChange}
            className="pure-input-1-2"
            placeholder="Title" />
          <textarea
            name="blogText"
            value={this.state.blogText}
            onChange={this.handleTextAreaChange}
            className="pure-input-1 blog-input"
            placeholder="Start here" />
        </div>
        <button type="submit" className="pure-button pure-input-1-3 pure-button-primary">Post</button>
      </form>
    )
  }
}

export default CreatePostForm

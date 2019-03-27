import * as React from "react";
import { Edit } from "react-feather";
import { Redirect } from "react-router-dom";

import * as config from "../../rabble_config.json";
import { IParsedPost } from "../models/posts";
import { RootComponent } from "./root_component";

interface IEditProps {
  username: string;
  display: boolean;
  blogPost: IParsedPost;
}

interface IEditState {
  redirect: boolean;
}

export class EditButton extends RootComponent<IEditProps, IEditState> {
  constructor(props: IEditProps) {
    super(props);

    this.state = {
      redirect: false,
    };

    this.handleEdit = this.handleEdit.bind(this);
  }

  public render() {
    if (!this.props.display) {
      return (<div/>);
    } else if (this.state.redirect) {
      const url = `/edit/${this.props.blogPost.global_id}`;
      return (<Redirect to={{ pathname: url }}/>);
    }
    return (
      <div onClick={this.handleEdit} className="pure-u-5-24">
        <Edit color="white" className="edit-icon"/>
      </div>
    );
  }

  private handleEdit() {
    this.setState({ redirect: true });
  }
}

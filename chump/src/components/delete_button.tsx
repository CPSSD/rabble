import * as React from "react";
import { Trash2 } from "react-feather";
import * as RModal from "react-modal";

import * as config from "../../rabble_config.json";
import { DeleteArticle } from "../models/article";
import { IParsedPost } from "../models/posts";
import { RootComponent } from "./root_component";

interface IDeleteProps {
  hideCallback: () => void;
  username: string;
  display: boolean;
  blogPost: IParsedPost;
}

export class DeleteButton extends RootComponent<IDeleteProps, {}> {
  constructor(props: IDeleteProps) {
    super(props);
    this.handleDelete = this.handleDelete.bind(this);
  }

  public render() {
    if (!this.props.display) {
      return (<div/>);
    }
    return (
      <div onClick={this.handleDelete} className="pure-u-3-24">
        <Trash2 color="white" className="edit-icon"/>
      </div>
    );
  }

  private handleDelete() {
    if (!window.confirm("Are you sure you want to delete this article?")) {
      return;
    }
    DeleteArticle(this.props.blogPost.global_id)
      .then((res: any) => {
        this.props.hideCallback();
      })
      .catch((err: any) => {
        this.alertUser(err);
      });
  }
}

import * as React from "react";
import { Trash2 } from "react-feather";
import * as RModal from "react-modal";
import * as request from "superagent";

import * as config from "../../rabble_config.json";
import { DeleteArticle } from "../models/article";
import { IParsedPost } from "../models/posts";
import { RootComponent } from "./root_component";

interface IDeleteProps {
  successCallback: () => void;
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
      return null;
    }
    return (
      <div onClick={this.handleDelete} className="pure-u-3-24">
        <Trash2 className="sub-post-icon"/>
      </div>
    );
  }

  private handleDelete() {
    if (!window.confirm(config.delete_confirm)) {
      return;
    }
    DeleteArticle(this.props.blogPost.global_id)
      .then((res: request.Response) => {
        if (res.status < 200 || res.status >= 300) {
          this.errorToast({ statusCode: res.status, debug: res });
          return;
        }

        this.props.successCallback();
      })
      .catch((err: Error) => {
        this.errorToast({ debug: err });
      });
  }
}

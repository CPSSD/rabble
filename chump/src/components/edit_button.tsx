import * as React from "react";
import { Edit } from "react-feather";

import * as config from "../../rabble_config.json";
import { IParsedPost } from "../models/posts";
import { RootComponent } from "./root_component";
// import { SendReblog } from "../models/reblog";

interface IEditProps {
  username: string;
  display: boolean;
  blogPost: IParsedPost;
}

export class EditButton extends RootComponent<IEditProps, {}> {
  constructor(props: IEditProps) {
    super(props);

    this.handleEdit = this.handleEdit.bind(this);
  }

  public render() {
    if (!this.props.display) {
      return (<div/>);
    }
    return (
      <div onClick={this.handleEdit} className="pure-u-5-24">
        <Edit color="white" className="edit-icon"/>
      </div>
    );
  }

  private handleEdit() {
    alert("Yo");
    // SendReblog(this.props.blogPost.global_id)
    //   .then((res: any) => {
    //     this.setState({
    //       isReblogged: true,
    //       sharesCount: this.state.sharesCount + 1,
    //     });
    //   })
    //   .catch((err: any) => {
    //     let message = err.message;
    //     if (err.response) {
    //       message = err.response.text;
    //     }
    //     this.alertUser(message);
    //   });
  }
}

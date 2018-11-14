import * as React from "react";
import { Link } from "react-router-dom";

import { IBlogPost } from "../models/posts";

interface IPostProps {
  blogPost: IBlogPost;
}

export class Post extends React.Component<IPostProps, {}> {
  constructor(props: IPostProps) {
    super(props);
    this.state = {};
  }

  public render() {
    // TODO(devoxel): Replace dangerouslySetInnerHTML with a safer option
    return (
      <div>
        <div className="pure-u-5-24"/>
        <div className="pure-u-10-24">
          <p className="article-byline">Published 1st January 1970</p>
          <h3 className="article-title">{this.props.blogPost.title}</h3>
          <p className="article-body" dangerouslySetInnerHTML={{ __html: this.props.blogPost.body }}/>
        </div>
        <div className="pure-u-1-24"/>
        <div className="pure-u-3-24">
          <div className="author-about">
            <img
              src="https://qph.fs.quoracdn.net/main-qimg-8aff684700be1b8c47fa370b6ad9ca13.webp"
              className="author-thumbnail"
            />
            <Link to={"/u/@" + this.props.blogPost.author} className="author-displayname">
              {this.props.blogPost.author}
            </Link><br/>
            <Link to={"/u/@" + this.props.blogPost.author} className="author-handle">
              @{this.props.blogPost.author}
            </Link>
            <p className="author-bio">Nowadays everybody wanna talk like they got something to say.
            But nothing comes out when they move their lips; just a bunch of gibberish.</p>
          </div>
        </div>
      </div>
    );
  }
}

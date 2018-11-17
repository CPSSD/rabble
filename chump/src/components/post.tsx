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
    return (
      <div className="blog-post-holder">
        <div className="pure-u-5-24"/>
        <div className="pure-u-10-24">
          <p className="article-byline">Published 1st January 1970</p>
          <Link
            to={`/@${this.props.blogPost.author}/${this.props.blogPost.global_id}`}
            className="article-title"
          >
            {this.props.blogPost.title}
          </Link>
          <p className="article-body" dangerouslySetInnerHTML={{ __html: this.props.blogPost.body }}/>
        </div>
        <div className="pure-u-1-24"/>
        <div className="pure-u-3-24">
          <div className="author-about">
            <img
              src="https://qph.fs.quoracdn.net/main-qimg-8aff684700be1b8c47fa370b6ad9ca13.webp"
              className="author-thumbnail"
            />
            <Link to={`/@${this.props.blogPost.author}`} className="author-displayname">
              {this.props.blogPost.author}
            </Link><br/>
            <Link to={`/@${this.props.blogPost.author}`} className="author-handle">
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

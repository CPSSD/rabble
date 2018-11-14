import * as React from "react";
import { Link } from "react-router-dom";

import { GetPublicPosts, IBlogPost } from "../models/posts";

interface IFeedProps {
  username: string;
}

interface IFeedState {
  publicBlog: IBlogPost[];
}

export class Feed extends React.Component<IFeedProps, IFeedState> {
  constructor(props: IFeedProps) {
    super(props);
    this.state = { publicBlog: [] };
  }

  public componentDidMount() {
    this.getPosts();
  }

  public getPosts() {
    GetPublicPosts(this.props.username)
      .then((posts: IBlogPost[]) => {
        this.setState({ publicBlog: posts });
      })
      .catch(this.handleGetPostsErr);
  }

  public handleGetPostsErr() {
    alert("could not communicate with server :(");
  }

  public renderPosts() {
    return this.state.publicBlog.map((e: IBlogPost, i: number) => {
      // TODO(devoxel): Replace dangerouslySetInnerHTML with a safer option
      return (
        <div className="pure-g" key={i}>
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <p className="article-byline">Published 1st January 1970</p>
            <h3 className="article-title">{e.title}</h3>
            <p className="article-body" dangerouslySetInnerHTML={{ __html: e.body }}/>
          </div>
          <div className="pure-u-1-24"/>
          <div className="pure-u-3-24">
            <div className="author-about">
              <img
                src="https://qph.fs.quoracdn.net/main-qimg-8aff684700be1b8c47fa370b6ad9ca13.webp"
                className="author-thumbnail"
              />
              <Link to="/" className="author-displayname">{e.author}</Link><br/>
              <Link to="/" className="author-handle">@{e.author}</Link>
              <p className="author-bio">Nowadays everybody wanna talk like they got something to say.
              But nothing comes out when they move their lips; just a bunch of gibberish.</p>
            </div>
          </div>
        </div>
      );
    });
  }

  public render() {
    const blogPosts = this.renderPosts();
    return (
      <div>
        <div className="pure-g">
          <div className="pure-u-5-24"/>
          <div className="pure-u-10-24">
            <h3 className="article-title">Your blog post could be here!</h3>
            <p>Check out our <Link to="/about">about</Link> page for more info!</p>
          </div>
        </div>
        {blogPosts}
      </div>
    );
  }
}

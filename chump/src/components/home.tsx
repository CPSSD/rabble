import * as React from "react";
import { Link } from "react-router-dom";

import { IBlogPost, GetPublicPosts } from "../api/posts"

interface IHomeState {
  publicBlog: IBlogPost[];
}

export class Home extends React.Component<{}, IHomeState> {
  constructor(props: any) {
    super(props);
    this.state = { publicBlog: [] };
  }

  componentDidMount() {
    this.getPosts(); 
  }

  getPosts() {
    GetPublicPosts().then((posts: IBlogPost[]) => {
      this.setState({ publicBlog: posts });
    });
  }

  renderPosts() {
    return this.state.publicBlog.map((e: IBlogPost, i: number) => {
      // TODO(aaronpd): Replace dangerouslySetInnerHTML with a safer option
      return (
        <div className="pure-g" key={i}>
          <div className="pure-u-1-5"/>
          <div className="pure-u-3-5">
            <h4> { e.title }, written by: { e.author }. </h4>
            <p dangerouslySetInnerHTML={{ __html: e.blogText }}/>
          </div>
        </div>
      );
    });
  }

  render() {
    const blogPosts = this.renderPosts()
    return (
      <div>
        <div className="pure-g">
          <div className="pure-u-1-5"/>
          <div className="pure-u-3-5">
            <h4>Your blog post could be here!</h4>
            <p>Check out our <Link to="/about">about</Link> page for more info!</p>
          </div>
        </div>
        {blogPosts}
      </div>
    );
  }
};

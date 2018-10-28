import * as Promise from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { MemoryRouter } from "react-router";
import * as sinon from "sinon";

import { IBlogPost } from "../src/models/posts";
import { Feed } from "../src/components/feed";
import { mount, shallow } from "./enzyme";

describe("Feed", () => {
  it("should call post collecting methods", () => {
    const getPosts = sinon.spy(Feed.prototype, "getPosts");
    const render = sinon.spy(Feed.prototype, "renderPosts");

    const wrapper = mount(<MemoryRouter><Feed/></MemoryRouter>);

    expect(getPosts).to.have.property("callCount", 1);
    expect(render).to.have.property("callCount", 1);

    // Cleanup spies
    getPosts.restore();
    render.restore();
  });

  it("should properly render posts", () => {
    const getPosts = sinon.spy(Feed.prototype, "getPosts");

    const wrapper = shallow(<Feed/>);
    expect(wrapper.find("div")).to.have.lengthOf(4);

    wrapper.setState({publicBlog: [
      {
        author: "sips",
        body: "id be in so much trouble<br>i'd never live it down<br>lol",
        title: "the man, the myth, the legend",
      },
    ]});

    expect(Feed.prototype.getPosts).to.have.property("callCount", 1);
    expect(wrapper.find("div")).to.have.lengthOf(7);

    // Cleanup spies
    getPosts.restore();
  });
});

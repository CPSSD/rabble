import * as bluebird from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { MemoryRouter } from "react-router";
import * as sinon from "sinon";

import { Feed } from "../../src/components/feed";
import { FeedBody } from "../../src/components/feed_body";
import * as posts from "../../src/models/posts";
import { mount, shallow } from "./enzyme";

const feedProps = {
  queryUserId: 0,
  username: "",
};
const now: Date = new Date();
const evalidBody: posts.IParsedPost[] = [{
  author: "aaron",
  author_display: "",
  author_host: "",
  author_id: 0,
  bio: "bio",
  body: "rm -rf steely/",
  global_id: 2,
  image: "",
  is_followed: false,
  is_liked: false,
  is_shared: false,
  likes_count: 1,
  md_body: "rm -rf rabble/",
  parsed_date: now,
  published: "",
  shares_count: 1,
  tags: [""],
  title: "how to write a plugin",
}];

describe("Feed", () => {
  it("should call post collecting methods", () => {
    const getPosts = sinon.spy(FeedBody.prototype, "getPosts");
    const render = sinon.spy(FeedBody.prototype, "renderPosts");

    const wrapper = mount(<MemoryRouter><Feed {...feedProps} /></MemoryRouter>);

    expect(getPosts).to.have.property("callCount", 1);
    expect(render).to.have.property("callCount", 1);

    // Cleanup spies
    getPosts.restore();
    render.restore();
  });

  it("should properly render posts", () => {
    const getPosts = sinon.spy(FeedBody.prototype, "getPosts");

    const getStub = sinon.stub(posts, "GetPublicPosts");
    const promise = new bluebird.Promise((resolve) => {
      resolve(evalidBody);
    });
    getStub.returns(promise);

    const wrapper = mount(<MemoryRouter><Feed {...feedProps} /></MemoryRouter>);

    expect(getPosts).to.have.property("callCount", 1);
    expect(wrapper.find("div")).to.have.lengthOf(4);

    // Cleanup spies
    getPosts.restore();
    getStub.restore();
  });
});

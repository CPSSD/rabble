import * as Promise from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { MemoryRouter } from "react-router";
import * as sinon from "sinon";

import { IParsedPost } from "../../src/models/posts";
import { SinglePost } from "../../src/components/single_post";
import { mount, shallow } from "./enzyme";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();

const postProps = {
  match: {
    params: {
      user: "test_user",
      article_id: "test_id",
    },
  },
  username: "nice",
};

describe("SinglePost", () => {

  afterEach(() => {
    sandbox.restore();
  });

  it("should call componentDidMount method", () => {
    const componentDidMount = sandbox.spy(SinglePost.prototype, "componentDidMount");
    const renderPost = sandbox.spy(SinglePost.prototype, "renderPost");

    const wrapper = mount(
      <MemoryRouter>
        <SinglePost {...postProps} />
      </MemoryRouter>
    );

    expect(componentDidMount).to.have.property("callCount", 1);
    expect(renderPost).to.have.property("callCount", 1);
  });

  it("should render page when there are no posts", () => {
    const wrapper = shallow(<SinglePost {...postProps} />);
    expect(wrapper.find("div")).to.have.lengthOf(4);
    expect(wrapper.find("Post")).to.have.lengthOf(0);
    expect(wrapper.find("p").text()).to.contain("404: Article not found");
  });

  it("should render page when there is a post", () => {
    const wrapper = shallow(<SinglePost {...postProps} />);
    wrapper.setState({posts: [
      {
        author: "sips",
        global_id: 3,
        body: "id be in so much trouble<br>i'd never live it down<br>lol",
        title: "the man, the myth, the legend",
      },
    ]});

    expect(wrapper.find("div")).to.have.lengthOf(2);
    expect(wrapper.find("Post")).to.have.lengthOf(1);
  });
});

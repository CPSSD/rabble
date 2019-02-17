import * as Promise from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { MemoryRouter } from "react-router";
import * as sinon from "sinon";

import { User } from "../../src/components/user_feed";
import { IParsedPost } from "../../src/models/posts";
import { mount, shallow } from "./enzyme";

describe("User", () => {
  it("should call post collecting methods", () => {
    const getPosts = sinon.spy(User.prototype, "getPosts");
    const render = sinon.spy(User.prototype, "renderPosts");

    const userProps = {
      match: {
        params: {
          user: "cian",
        },
      },
      username: "",
    };
    const wrapper = mount(
      <MemoryRouter>
        <User {...userProps} />
      </MemoryRouter>,
    );

    expect(getPosts).to.have.property("callCount", 1);
    expect(render).to.have.property("callCount", 1);

    // Cleanup spies
    getPosts.restore();
    render.restore();
  });

  it("should properly render posts", () => {
    const userProps = {
      match: {
        params: {
          user: "sips",
        },
      },
      username: "",
    };
    const wrapper = shallow(<User {...userProps} />);
    expect(wrapper.find("div")).to.have.lengthOf(4);
    expect(wrapper.find("Post")).to.have.lengthOf(0);

    wrapper.setState({publicBlog: [
      {
        author: "sips",
        body: "id be in so much trouble<br>i'd never live it down<br>lol",
        title: "the man, the myth, the legend",
      },
    ]});

    expect(wrapper.find("div")).to.have.lengthOf(2);
    expect(wrapper.find("Post")).to.have.lengthOf(1);
  });

  it("should render user links when user is looking at their own page", () => {
    const userProps = {
      match: {
        params: {
          user: "sips",
        },
      },
      username: "sips",
    };
    const wrapper = shallow(<User {...userProps} />);
    expect(wrapper.find("div")).to.have.lengthOf(7);
    expect(wrapper.find("Post")).to.have.lengthOf(0);
  });

});

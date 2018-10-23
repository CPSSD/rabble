import * as Promise from 'bluebird';
import { expect } from "chai";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { MemoryRouter } from "react-router";
import * as sinon from 'sinon';

import { IBlogPost } from "../src/api/posts"
import { Home } from "../src/components/home";
import { mount, shallow } from "./enzyme";

describe("Home", () => {
  it("should call post collecting methods", () => {
    const getPosts = sinon.spy(Home.prototype, 'getPosts');
    const render = sinon.spy(Home.prototype, 'renderPosts');

    const wrapper = mount(<MemoryRouter><Home/></MemoryRouter>);

    expect(getPosts).to.have.property('callCount', 1);
    expect(render).to.have.property('callCount', 1);

    // Cleanup spies
    getPosts.restore();
    render.restore();
  });

  it("should properly render posts", () => {
    const getPosts = sinon.spy(Home.prototype, 'getPosts')
    
    const wrapper = shallow(<Home/>);
    expect(wrapper.find('div')).to.have.lengthOf(4)

    wrapper.setState({publicBlog: [
      {
        author: "sips",
        title: "the man, the myth, the legend",
        blogText: "id be in so much trouble<br>i'd never live it down<br>lol",
      },
    ]})

    expect(Home.prototype.getPosts).to.have.property('callCount', 1);
    expect(wrapper.find('div')).to.have.lengthOf(7)

    // Cleanup spies
    getPosts.restore();
  });
});

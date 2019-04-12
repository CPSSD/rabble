import { expect } from "chai";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { MemoryRouter } from "react-router";

import { About } from "../../src/components/about";
import { HeaderWithRouter } from "../../src/components/header";
import { render, shallow } from "./enzyme";

describe("About", () => {
  it("should render correctly", () => {
    const wrapper = shallow(<About/>);
    expect(wrapper.find("div")).to.have.lengthOf(4);
  });
});

describe("Header", () => {
  it("should render correctly", () => {
    // Since we"re doing a real render, we need a parent router.
    const wrapper = render(
      <MemoryRouter>
        <HeaderWithRouter username={"x0x"} userId={0}/>
      </MemoryRouter>
    );
    expect(wrapper.find("a").text()).to.contain("Rabble");
    expect(wrapper.find(".pure-menu-link").text()).to.contain("Write");
    expect(wrapper.find(".pure-menu-link").text()).to.contain("x0x");
  });
});

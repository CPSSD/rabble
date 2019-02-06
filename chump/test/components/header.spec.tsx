import { expect } from "chai";
import * as React from "react";
import { HashRouter } from "react-router-dom";
import * as sinon from "sinon";

import { Header } from "../../src/components/header";
import { mount } from "../enzyme";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();

let testComponent: any;

function mountHeader() {
  testComponent = mount(
    <HashRouter>
      <div>
        <Header username={"ross"}/>
      </div>
    </HashRouter>,
  );
}

describe("Header", () => {

  afterEach(() => {
    sandbox.restore();
    testComponent.unmount();
  });

  it("can mount logged in", (done) => {
    mountHeader();
    expect(testComponent.exists(".search-form")).to.equal(true);
    expect(testComponent.exists(".pure-menu-has-children")).to.equal(true);
    done();
  });

  it("can mount logged out", (done) => {
    testComponent = mount(
      <HashRouter>
        <div>
          <Header username={""}/>
        </div>
      </HashRouter>,
    );
    expect(testComponent.exists(".search-form")).to.equal(true);
    expect(testComponent.exists(".pure-menu-has-children")).to.equal(false);
    done();
  });

  it("can handle query input", (done) => {
    mountHeader();
    testComponent.find("[name=\"query\"]")
      .simulate("change", {
        target: {
          name: "query",
          value: "It's a me Mario",
        },
      });
    expect(testComponent.find("Header").state()).to.have.property("query", "It's a me Mario");
    done();
  });

  it("can submit query form", (done) => {
    const submitStub: any = sandbox.stub(Header.prototype, "handleSubmitSearch" as any);
    mountHeader();
    testComponent.find("form").first().simulate("submit");
    expect(submitStub.called).to.equal(true);
    done();
  });

  describe ("dropdown menu", () => {
    it("can be displayed", (done) => {
      mountHeader();
      testComponent.find(".button-link").first().simulate("click");
      expect(testComponent.find("Header").state()).to.have.property("display", "inherit");
      done();
    });

    it("can be hidden", (done) => {
      mountHeader();
      testComponent.find("Header").setState({ display: "inherit" });
      testComponent.find(".button-link").first().simulate("click");
      expect(testComponent.find("Header").state()).to.have.property("display", "none");
      done();
    });

    it("can be hidden by clicking other menu option", (done) => {
      mountHeader();
      testComponent.find("Header").setState({ display: "inherit" });
      testComponent.find(".brand").first().simulate("click");
      expect(testComponent.find("Header").state()).to.have.property("display", "none");
      done();
    });
  });
});

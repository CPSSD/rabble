import { expect } from "chai";
import * as React from "react";
import { HashRouter } from "react-router-dom";
import * as sinon from "sinon";

import { HeaderWithRouter } from "../../src/components/header";
import { mount } from "./enzyme";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();

let testComponent: any;

function mountHeaderWithRouter() {
  testComponent = mount(
    <HashRouter>
      <div>
        <HeaderWithRouter username={"ross"} userId={1}/>
      </div>
    </HashRouter>,
  );
}

describe("HeaderWithRouter", () => {

  afterEach(() => {
    sandbox.restore();
    testComponent.unmount();
  });

  it("can mount logged in", (done) => {
    mountHeaderWithRouter();
    expect(testComponent.exists(".search-form")).to.equal(true);
    expect(testComponent.exists(".pure-menu-has-children")).to.equal(true);
    done();
  });

  it("can mount logged out", (done) => {
    testComponent = mount(
      <HashRouter>
        <div>
          <HeaderWithRouter username={""} userId={0}/>
        </div>
      </HashRouter>,
    );
    expect(testComponent.exists(".search-form")).to.equal(true);
    expect(testComponent.exists(".pure-menu-has-children")).to.equal(false);
    done();
  });

  it("can handle query input", (done) => {
    mountHeaderWithRouter();
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

  describe ("dropdown menu", () => {
    it("can be displayed", (done) => {
      mountHeaderWithRouter();
      testComponent.find(".button-link").first().simulate("click");
      expect(testComponent.find("Header").state()).to.have.property("display", "inherit");
      done();
    });

    it("can be hidden", (done) => {
      mountHeaderWithRouter();
      testComponent.find("Header").setState({ display: "inherit" });
      testComponent.find(".button-link").first().simulate("click");
      expect(testComponent.find("Header").state()).to.have.property("display", "none");
      done();
    });

    it("can be hidden by clicking other menu option", (done) => {
      mountHeaderWithRouter();
      testComponent.find("Header").setState({ display: "inherit" });
      testComponent.find(".brand").first().simulate("click");
      expect(testComponent.find("Header").state()).to.have.property("display", "none");
      done();
    });
  });
});

import * as bluebird from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as sinon from "sinon";

import { FollowForm } from "../../src/components/follow_form";
import { PartialResponse} from "../../src/models/common";
import * as follow from "../../src/models/follow";
import { mount } from "./enzyme";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();

function genResponse(statusCode: number): PartialResponse {
  return {
    status: statusCode,
  };
}

describe("FollowForm", () => {
  let testComponent: any;
  let followStub: any;
  let errorStub: any;
  let successStub: any;

  afterEach(() => {
    sandbox.restore();
    testComponent.unmount();
  });

  it("can mount", (done) => {
    testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
    done();
  });

  it("can handle toFollow input", (done) => {
    testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
    testComponent.find("[name=\"toFollow\"]")
      .simulate("change", {
        target: {
          name: "toFollow",
          value: "pam",
        },
      });
    expect(testComponent.state()).to.have.property("toFollow", "pam");
    done();
  });

  it("can handle type input", (done) => {
    testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
    testComponent.find("[id=\"type\"]")
      .simulate("change", {
        target: {
          name: "type",
          value: "url",
        },
      });
    expect(testComponent.state()).to.have.property("type", "url");
    done();
  });

  it("can submit form", (done) => {
    const submitStub: any = sandbox.stub(FollowForm.prototype, "handleSubmitForm" as any);
    testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
    testComponent.find("form").first().simulate("submit");
    expect(submitStub.called).to.equal(true);
    done();
  });

  describe("can call Follow model for create follow", () => {
    beforeEach(() => {
      followStub = sandbox.stub(follow, "CreateFollow");
      errorStub = sandbox.stub(FollowForm.prototype, "errorToast" as any);
      successStub = sandbox.stub(FollowForm.prototype, "successToast" as any);
    });

    it("and handle success", (done) => {
      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      const promise = new bluebird.Promise((resolve) => {
        resolve(genResponse(200));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      promise.finally(() => {
        expect(errorStub.notCalled).to.equal(true);
        expect(successStub.called).to.equal(true);
        done();
      });
    });

    it("and handle a non 200 status code", (done) => {
      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        resolve(genResponse(400));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(successStub.notCalled).to.equal(true);
        expect(errorStub.called).to.equal(true);
        done();
      }, 200);
    });

    it("and handle exceptions", (done) => {
      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error("BAD!"));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(successStub.notCalled).to.equal(true);
        expect(errorStub.called).to.equal(true);
        done();
      }, 200);
    });
  });
  describe("can call Follow model for rss follow", () => {

    beforeEach(() => {
      followStub = sandbox.stub(follow, "CreateRssFollow");
      errorStub = sandbox.stub(FollowForm.prototype, "errorToast" as any);
      successStub = sandbox.stub(FollowForm.prototype, "successToast" as any);

      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      testComponent.find("[id=\"type\"]")
        .simulate("change", {
          target: {
            name: "type",
            value: "url",
          },
        });
    });

    it("and handle success", (done) => {
      const promise = new bluebird.Promise((resolve) => {
        resolve(genResponse(200));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      promise.finally(() => {
        expect(errorStub.notCalled).to.equal(true);
        expect(successStub.called).to.equal(true);
        done();
      });
    });

    it("and handle a non 200 status code", (done) => {
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error("rip cpssd"));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(errorStub.called).to.equal(true);
        expect(successStub.notCalled).to.equal(true);
        done();
      }, 200);
    });

    it("and handle exeptions", (done) => {
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error("OwO whats this"));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(errorStub.called).to.equal(true);
        expect(successStub.notCalled).to.equal(true);
        done();
      }, 200);
    });
  });
});

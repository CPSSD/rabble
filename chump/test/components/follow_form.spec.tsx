import * as bluebird from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as sinon from "sinon";

import { FollowForm } from "../../src/components/follow_form";
import * as follow from "../../src/models/follow";
import { mount } from "./enzyme";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();

describe("FollowForm", () => {
  let testComponent: any;
  let followStub: any;
  let alertStub: any;

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
      alertStub = sandbox.stub(FollowForm.prototype, "alertUser" as any);
    });

    it("and handle success", (done) => {
      const responseMessage: string = "{}";
      const expectedMessage: string = "Posted follow with response: {}";
      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      const promise = new bluebird.Promise((resolve) => {
        resolve({ text: responseMessage });
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      promise.finally(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(expectedMessage)).to.equal(true);
        done();
      });
    });

    it("and handle a 403: permission denied", (done) => {
      const alertMessage: string = "403";
      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });

    it("and handle a 400: bad request", (done) => {
      const alertMessage: string = "400";
      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });

    it("and handle other error", (done) => {
      const alertMessage: string = "500";
      testComponent = mount(<FollowForm username={"johannes"} userId={0}/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });
  });
  describe("can call Follow model for rss follow", () => {

    beforeEach(() => {
      followStub = sandbox.stub(follow, "CreateRssFollow");
      alertStub = sandbox.stub(FollowForm.prototype, "alertUser" as any);
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
      const responseMessage: string = "{}";
      const expectedMessage: string = "Posted follow with response: {}";
      const promise = new bluebird.Promise((resolve) => {
        resolve({ text: responseMessage });
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      promise.finally(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(expectedMessage)).to.equal(true);
        done();
      });
    });

    it("and handle a 403: permission denied", (done) => {
      const alertMessage: string = "403";
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });

    it("and handle a 400: bad request", (done) => {
      const alertMessage: string = "400";
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });

    it("and handle other error", (done) => {
      const alertMessage: string = "500";
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      followStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(followStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });
  });
});

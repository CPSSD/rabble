import * as bluebird from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as sinon from "sinon";

import CreateArticleForm from "../../src/components/create_article_form";
import * as article from "../../src/models/article";
import { mount } from "../enzyme";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();

describe("CreateArticleForm", () => {
  let testComponent: any;
  let createStub: any;
  let alertStub: any;

  afterEach(() => {
    sandbox.restore();
    testComponent.unmount();
  });

  it("can mount", (done) => {
    testComponent = mount(<CreateArticleForm/>);
    done();
  });

  it("can handle username input", (done) => {
    testComponent = mount(<CreateArticleForm/>);
    testComponent.find("[name=\"username\"]")
      .simulate("change", {
          target: {
            name: "username",
            value: "greatusername",
          },
        });
    expect(testComponent.state()).to.have.property("username", "greatusername");
    done();
  });

  it("can handle title input", (done) => {
    testComponent = mount(<CreateArticleForm/>);
    testComponent.find("[name=\"title\"]")
      .simulate("change", {
        target: {
          name: "title",
          value: "Great Title",
        },
      });
    expect(testComponent.state()).to.have.property("title", "Great Title");
    done();
  });

  it("can handle TextArea input", (done) => {
    testComponent = mount(<CreateArticleForm/>);
    testComponent.find("[name=\"blogText\"]")
      .simulate("change", {
        target: {
          name: "blogText",
          value: "Clickbait",
        },
      });
    expect(testComponent.state()).to.have.property("blogText", "Clickbait");
    done();
  });

  it("can submit form", (done) => {
    const submitStub: any = sandbox.stub(CreateArticleForm.prototype, "handleSubmitForm" as any);
    testComponent = mount(<CreateArticleForm/>);
    testComponent.find("form").first().simulate("submit");
    expect(submitStub.called).to.equal(true);
    done();
  });

  describe("can call Article model for create article", () => {

    beforeEach(() => {
      createStub = sandbox.stub(article, "CreateArticle");
      alertStub = sandbox.stub(CreateArticleForm.prototype, "alertUser" as any);
    });

    it("and handle success", (done) => {
      const alertMessage: string = "Request went well";
      testComponent = mount(<CreateArticleForm/>);
      const promise = new bluebird.Promise((resolve) => {
        resolve({ text: alertMessage });
      });
      createStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(createStub.called).to.equal(true);
      promise.finally(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      });
    });

    it("and handle a 403: permission denied", (done) => {
      const alertMessage: string = "403";
      testComponent = mount(<CreateArticleForm/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      createStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(createStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);

    });

    it("and handle a 400: bad request", (done) => {
      const alertMessage: string = "400";
      testComponent = mount(<CreateArticleForm/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      createStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(createStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });

    it("and handle other error", (done) => {
      const alertMessage: string = "500";
      testComponent = mount(<CreateArticleForm/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error(alertMessage));
      });
      createStub.returns(promise);
      testComponent.find("form").first().simulate("submit");
      expect(createStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        expect(alertStub.calledWith(alertMessage)).to.equal(true);
        done();
      }, 200);
    });
  });
});

import * as bluebird from "bluebird";
import { expect } from "chai";
import * as React from "react";
import * as sinon from "sinon";
import * as request from "superagent";

import { CreateArticleForm } from "../../src/components/create_article_form";
import * as article from "../../src/models/article";
import { mount } from "./enzyme";
import { PartialResponse} from "../../src/models/common";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();
const now: Date = new Date();

const examplePost = {
  author: "sips",
  body: "id be in so much trouble<br>i'd never live it down<br>lol",
  global_id: 3,
  likes_count: 1,
  parsed_date: now,
  published: "",
  shares_count: 1,
  tags: ["test"],
  title: "the man, the myth, the legend",
};

const exampleProps = {
  onSubmit: () =>  new bluebird((r: any, _: any) => { r(); }),
  prefillState: () => { return; },
  username:  "sips",
  successMessage: "happy farts",
};

function genCreateResponse(statusCode: number): PartialResponse {
  return {
    status: statusCode,
    body: examplePost,
  };
}

describe("CreateArticleForm", () => {
  let testComponent: any;
  let createStub: any;
  let previewStub: any;
  let alertStub: any;
  let successStub: any;

  afterEach(() => {
    sandbox.restore();
    testComponent.unmount();
  });

  it("can mount", (done) => {
    testComponent = mount(<CreateArticleForm {...exampleProps}/>);
    done();
  });

  it("can handle title input", (done) => {
    testComponent = mount(<CreateArticleForm {...exampleProps}/>);
    testComponent.find("[name=\"title\"]").simulate("change", {
        target: {
          name: "title",
          value: "Great Title",
        },
      });
    expect(testComponent.state()).to.have.property("title", "Great Title");
    done();
  });

  it("can handle TextArea input", (done) => {
    testComponent = mount(<CreateArticleForm {...exampleProps}/>);
    testComponent.find("[name=\"blogText\"]").simulate("change", {
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
    testComponent = mount(<CreateArticleForm {...exampleProps}/>);
    testComponent.find("form").first().simulate("submit");
    expect(submitStub.called).to.equal(true);
    done();
  });

  describe("can call Article model for create article", () => {
    beforeEach(() => {
      alertStub = sandbox.stub(CreateArticleForm.prototype, "errorToast" as any);
      successStub = sandbox.stub(CreateArticleForm.prototype, "successToast" as any);
      createStub = sandbox.stub();
    });

    it("and handle success", (done) => {
      const response = genCreateResponse(200);
      const promise = new bluebird.Promise((resolve) => {
        resolve(response);
      });
      createStub.returns(promise);
      testComponent = mount(<CreateArticleForm {...exampleProps} onSubmit={createStub}/>);
      testComponent.find("[name=\"title\"]").simulate("change", {
        target: {
          name: "title",
          value: "Great Title",
        },
      });
      testComponent.find("form").first().simulate("submit");
      expect(createStub.called).to.equal(true);
      promise.finally(() => {
        expect(alertStub.notCalled).to.equal(true);
        expect(successStub.called).to.equal(true);
        done();
      });
    });

  it("and block submissions without a title", (done) => {
    const alertMessage: string = "A post cannot have an empty title";
    testComponent = mount(<CreateArticleForm {...exampleProps}/>);
    testComponent.find("form").first().simulate("submit");
    expect(alertStub.called).to.equal(true);
    done();
  });

  it("and handle a non 200 status code", (done) => {
    const response = genCreateResponse(403);
    const promise = new bluebird.Promise((resolve) => {
      resolve(response);
    });
    createStub.returns(promise);

    testComponent = mount(<CreateArticleForm {...exampleProps} onSubmit={createStub}/>);
    testComponent.find("[name=\"title\"]").simulate("change", {
        target: {
          name: "title",
          value: "Great Title",
        },
      });
    testComponent.find("form").first().simulate("submit");
    expect(createStub.called).to.equal(true);
    setTimeout(() => {
      expect(successStub.notCalled).to.equal(true);
      expect(alertStub.called).to.equal(true);
      done();
    }, 200);
  });

  it("handle an exception", (done) => {
    const err = new Error("bad stuff");
    const promise = new bluebird.Promise((resolve, reject) => {
      reject(err);
    });
    createStub.returns(promise);

    testComponent = mount(<CreateArticleForm {...exampleProps} onSubmit={createStub}/>);
    testComponent.find("[name=\"title\"]").simulate("change", {
      target: {
        name: "title",
        value: "Great Title",
      },
    });

    testComponent.find("form").first().simulate("submit");
    expect(createStub.called).to.equal(true);
    setTimeout(() => {
      expect(successStub.notCalled).to.equal(true);
      expect(alertStub.called).to.equal(true);
      done();
    }, 200);
  });
});

  describe("can handle previewing", () => {
    beforeEach(() => {
      previewStub = sandbox.stub(article, "CreatePreview");
      alertStub = sandbox.stub(CreateArticleForm.prototype, "errorToast" as any);
    });

    it("successfully get and show preview", (done) => {
      const response = genCreateResponse(200);
      const promise = new bluebird.Promise((resolve) => {
        resolve(response);
      });
      previewStub.returns(promise);

      testComponent = mount(<CreateArticleForm {...exampleProps} onSubmit={createStub}/>);
      testComponent.find("button").at(0).simulate("click");
      expect(previewStub.called).to.equal(true);
      promise.finally(() => {
        expect(testComponent.state()).to.have.property("showModal", true);
        expect(testComponent.state().post).to.have.property("author", "sips");
        done();
      });
    });

    it("and successfully post from preview", (done) => {

      const submitStub: any = sandbox.stub(CreateArticleForm.prototype, "handleSubmitForm" as any);
      const response = genCreateResponse(200);
      const promise = new bluebird.Promise((resolve) => {
        resolve(response);
      });
      const alertMessage: string = "Request went well";
      const createPromise = new bluebird.Promise((resolve) => {
        resolve(alertMessage);
      });
      testComponent = mount(<CreateArticleForm {...exampleProps}/>);
      previewStub.returns(promise);
      createStub.returns(createPromise);

      testComponent.find("[name=\"title\"]").simulate("change", {
          target: {
            name: "title",
            value: "Great Title",
          },
        });
      testComponent.find("button").at(0).simulate("click");
      expect(previewStub.called).to.equal(true);
      promise.finally(() => {
        expect(testComponent.state()).to.have.property("showModal", true);
        expect(testComponent.state().post).to.have.property("author", "sips");
        testComponent.update();
        testComponent.find(".preview-post").first().simulate("click");
        expect(submitStub.called).to.equal(true);
        done();
      });
    });

    it("and handle req error", (done) => {
      testComponent = mount(<CreateArticleForm {...exampleProps}/>);
      const promise = new bluebird.Promise((resolve, reject) => {
        reject(new Error("cpssd will last. haha jk"));
      });
      previewStub.returns(promise);
      testComponent.find("[name=\"title\"]").simulate("change", {
          target: {
            name: "title",
            value: "Great Title",
          },
        });
      testComponent.find("button").at(0).simulate("click");
      expect(previewStub.called).to.equal(true);
      setTimeout(() => {
        expect(alertStub.called).to.equal(true);
        done();
      }, 200);
    });
  });
});

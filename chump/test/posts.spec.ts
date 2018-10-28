/* tslint:disable:no-unused-expression */
import * as Promise from "bluebird";
import { expect } from "chai";
import * as sinon from "sinon";
import * as superagent from "superagent";

import { GetPublicPosts, IBlogPost } from "../src/models/posts";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();

function createFakeResponse(body: IBlogPost[] | Error | null) {
  const end = (cb: any) => {
      cb(null, {ok: true, body });
  };
  const set = () => ({ end });
  const root = { set };
  return sandbox.stub(superagent, "get").returns(root);
}

const validBody: IBlogPost[] = [{
  author: "aaron",
  body: "rm -rf steely/",
  global_id: "2",
  title: "how to write a plugin",
}];

describe("GetPublicPosts", () => {

  afterEach(() => {
    sandbox.restore();
  });

  it("should call api", (done) => {
    const getRequest = createFakeResponse(validBody);
    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      expect(posts).to.eql(validBody);
      done();
    });
  });

  it("should handle a username", (done) => {
    const getRequest = createFakeResponse(validBody);
    GetPublicPosts("username").then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed/username")).to.be.ok;
      expect(posts).to.eql(validBody);
      done();
    });
  });

  it("should handle a null response", (done) => {
    const getRequest = createFakeResponse(null);
    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      expect(posts).to.eql([]);
      done();
    });
  });

  it("should handle an error", (done) => {
    const getRequest = createFakeResponse(Error("bad"));
    GetPublicPosts().then(() => {
      expect.fail();
      done();
    }).catch(() => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      done();
    });
  });
});

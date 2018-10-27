/* tslint:disable:no-unused-expression */
import * as Promise from "bluebird";
import { expect } from "chai";
import * as sinon from "sinon";
import * as superagent from "superagent";

import { GetPublicPosts, IBlogPost } from "../src/api/posts";

function createFakeResponse(body: IBlogPost[] | Error | null) {
  const end = (cb: any) => {
      cb(null, {ok: true, body, });
  }
  const send = () => ({ end });
  const set = () => ({ send });
  const root = { set };
  return sinon.stub(superagent, "get").returns(root);
}

describe("GetPublicPosts", () => {
  it("should call api", (done) => {
    const fakeBody: IBlogPost[] = [{
      author: "aaron",
      body: "rm -rf steely/",
      global_id: "2",
      title: "how to write a plugin",
    }];
    const getRequest = createFakeResponse(fakeBody);
    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      expect(posts).to.eql(fakeBody);
      done();
    });
    getRequest.restore();
  });

  it("should handle a null response", (done) => {
    const getRequest = createFakeResponse(null);
    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      expect(posts).to.eql([]);
      done();
    });
    getRequest.restore();
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

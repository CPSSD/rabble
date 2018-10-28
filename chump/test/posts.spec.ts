/* tslint:disable:no-unused-expression */
import * as Promise from "bluebird";
import { expect } from "chai";
import * as sinon from "sinon";
import * as superagent from "superagent";

import { GetPublicPosts, IBlogPost } from "../src/api/posts";

describe("GetPublicPosts", () => {
  it("should call api", (done) => {

    const fakeBody: IBlogPost[] = [{
      author: "aaron",
      body: "rm -rf steely/",
      global_id: "2",
      title: "how to write a plugin",
    }];
    const getRequest = sinon.stub(superagent, "get").returns({
      set: () => {
        return ({
          end: (cb: any) => {
            cb(null, {ok: true, body: fakeBody });
          },
        });
      },
    });

    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      expect(posts).to.eql(fakeBody);
      done();
    });

    getRequest.restore();
  });

  it("should handle a null response", (done) => {

    const getRequest = sinon.stub(superagent, "get").returns({
      set: () => {
        return ({
          end: (cb: any) => {
            cb(null, {ok: true, body: null });
          },
        });
      },
    });

    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      expect(posts).to.eql([]);
      done();
    });

    getRequest.restore();

  });

  it("should handle an error", (done) => {
    const getRequest = sinon.stub(superagent, "get").returns({
      set: () => {
        return ({
          end: (cb: any) => {
            cb(new Error("bad!"), {ok: true, body: {}});
          },
        });
      },
    });

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

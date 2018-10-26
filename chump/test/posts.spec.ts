import * as Promise from 'bluebird';
import { expect } from "chai";
import * as superagent from 'superagent';
import * as sinon from "sinon";

import { IBlogPost, GetPublicPosts } from "../src/api/posts"

describe("GetPublicPosts", () => {
  it("should call api", (done) => {
    const getRequest = sinon.stub(superagent, 'get').returns({
      set: () => {
        return ({
          end: (cb: any) => {
            cb(null, {ok: true, body: {}});
          }
        });
      },
    });

    GetPublicPosts().then((posts: IBlogPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      done();
    });

    getRequest.restore();
  });

  it("should handle an error", (done) => {
    const getRequest = sinon.stub(superagent, 'get').returns({
      set: () => {
        return ({
          end: (cb: any) => {
            cb(new Error("bad!"), {ok: true, body: {}});
          }
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
})

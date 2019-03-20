/* tslint:disable:no-unused-expression */
import * as Promise from "bluebird";
import { expect } from "chai";
import * as sinon from "sinon";
import * as superagent from "superagent";

import { GetPublicPosts, GetSinglePost, IFeedResponse, IParsedPost } from "../../src/models/posts";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();
const now: Date = new Date();

function createFakeResponse(body: IFeedResponse | Error | null) {
  const end = (cb: any) => {
      cb(null, {ok: true, body });
  };
  const set = () => ({ end });
  const root = { set };
  return sandbox.stub(superagent, "get").returns(root);
}

const validBody: IFeedResponse = {
  post_body_css: "",
  post_title_css: "",
  results: [{
    author: "aaron",
    author_display: "",
    author_host: "",
    author_id: 0,
    bio: "bio",
    body: "rm -rf steely/",
    global_id: 2,
    image: "",
    is_followed: false,
    is_liked: false,
    is_shared: false,
    likes_count: 1,
    published: "",
    shares_count: 1,
    title: "how to write a plugin",
  }],
  share_results: [],
};

const evalidBody: IParsedPost[] = [{
  author: "aaron",
  author_display: "",
  author_host: "",
  author_id: 0,
  bio: "bio",
  body: "rm -rf steely/",
  global_id: 2,
  image: "",
  is_followed: false,
  is_liked: false,
  is_shared: false,
  likes_count: 1,
  parsed_date: now,
  published: "",
  shares_count: 1,
  title: "how to write a plugin",
}];

describe("GetPublicPosts", () => {

  afterEach(() => {
    sandbox.restore();
  });

  it("should call api", (done) => {
    const getRequest = createFakeResponse(validBody);
    GetPublicPosts().then((posts: IParsedPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed")).to.be.ok;
      expect(posts).to.eql(validBody.results);
      done();
    });
  });

  it("should handle a username", (done) => {
    const getRequest = createFakeResponse(validBody);
    GetPublicPosts("username").then((posts: IParsedPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/feed/username")).to.be.ok;
      expect(posts).to.eql(validBody.results);
      done();
    });
  });

  it("should handle a null response", (done) => {
    const getRequest = createFakeResponse(null);
    GetPublicPosts().then((posts: IParsedPost[]) => {
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

  it("should handle a single Post request", (done) => {
    const getRequest = createFakeResponse(validBody);
    GetSinglePost("id").then((posts: IParsedPost[]) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith("/c2s/@5/id")).to.be.ok;
      expect(posts).to.eql(validBody.results);
      done();
    });
  });
});

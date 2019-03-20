import * as Promise from "bluebird";
import { expect } from "chai";
import * as sinon from "sinon";
import * as superagent from "superagent";

import { IParsedPost } from "../../src/models/posts";
import { IParsedUser, ISearchResponse, SearchRequest } from "../../src/models/search";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();
const now: Date = new Date();

function createFakeResponse(body: ISearchResponse | Error | null) {
  const end = (cb: any) => {
      cb(null, {ok: true, body });
  };
  const retry = () => ({ end });
  const set = () => ({ retry });
  const root = { set };
  return sandbox.stub(superagent, "get").returns(root);
}

const validParsedPost: IParsedPost[] = [{
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

const validUser: IParsedUser[] = [{
  bio: "bio",
  display_name: "the.aaron",
  global_id: "4",
  handle: "aaron",
  host: "google.com",
  image: "test",
  is_followed: true,
}];

const validBody: ISearchResponse = {
  posts: validParsedPost,
  users: validUser,
};

describe("Search", () => {

  afterEach(() => {
    sandbox.restore();
  });

  it("should call api", (done) => {
    const getRequest = createFakeResponse(validBody);
    SearchRequest("test").then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="test"')).to.equal(true);
      expect(resp).to.eql(validBody);
      done();
    });
  });

  it("should handle no query", (done) => {
    const getRequest = createFakeResponse(validBody);
    SearchRequest().then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query=""')).to.equal(true);
      expect(resp).to.eql(validBody);
      done();
    });
  });

  it("should handle encoded query", (done) => {
    const getRequest = createFakeResponse(validBody);
    SearchRequest("who?").then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="who%3F"')).to.equal(true);
      expect(resp).to.eql(validBody);
      done();
    });
  });

  it("should handle a null response", (done) => {
    const getRequest = createFakeResponse(null);
    SearchRequest("test").then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="test"')).to.equal(true);
      expect(resp).to.eql({ users: [], posts: []});
      done();
    });
  });

  it("should handle an error", (done) => {
    const getRequest = createFakeResponse(Error("bad"));
    SearchRequest("test").then(() => {
      expect.fail();
      done();
    }).catch(() => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="test"')).to.equal(true);
      done();
    });
  });
});

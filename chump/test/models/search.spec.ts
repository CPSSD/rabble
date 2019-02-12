import * as Promise from "bluebird";
import { expect } from "chai";
import * as sinon from "sinon";
import * as superagent from "superagent";

import { IParsedPost } from "../../src/models/posts";
import { IParsedUser, ISearchResponse, Search } from "../../src/models/search";

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
  bio: "bio",
  body: "rm -rf steely/",
  global_id: 2,
  image: "",
  is_liked: false,
  likes_count: 1,
  parsed_date: now,
  published: "",
  title: "how to write a plugin",
}];

const validUser: IParsedUser[] = [{
  bio: "bio",
  global_id: "4",
  handle: "aaron",
  host: "google.com",
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
    Search("test").then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="test"')).to.equal(true);
      expect(resp).to.eql(validBody);
      done();
    });
  });

  it("should handle no query", (done) => {
    const getRequest = createFakeResponse(validBody);
    Search().then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query=""')).to.equal(true);
      expect(resp).to.eql(validBody);
      done();
    });
  });

  it("should handle encoded query", (done) => {
    const getRequest = createFakeResponse(validBody);
    Search("who?").then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="who%3F"')).to.equal(true);
      expect(resp).to.eql(validBody);
      done();
    });
  });

  it("should handle a null response", (done) => {
    const getRequest = createFakeResponse(null);
    Search("test").then((resp: ISearchResponse) => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="test"')).to.equal(true);
      expect(resp).to.eql({ users: [], posts: []});
      done();
    });
  });

  it("should handle an error", (done) => {
    const getRequest = createFakeResponse(Error("bad"));
    Search("test").then(() => {
      expect.fail();
      done();
    }).catch(() => {
      expect(getRequest).to.have.property("callCount", 1);
      expect(getRequest.calledWith('/c2s/search?query="test"')).to.equal(true);
      done();
    });
  });
});

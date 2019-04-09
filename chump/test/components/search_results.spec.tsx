import * as bluebird from "bluebird";
import { expect } from "chai";
import * as React from "react";
import { HashRouter } from "react-router-dom";
import * as sinon from "sinon";

import { SearchResults } from "../../src/components/search_results";
import { IParsedPost } from "../../src/models/posts";
import * as Search from "../../src/models/search";
import { IParsedUser } from "../../src/models/user";
import { mount } from "./enzyme";

const sandbox: sinon.SinonSandbox = sinon.createSandbox();
const now: Date = new Date();

let alertStub: any;
let testComponent: any;
let searchRequestStub: any;
let searchRequestPromise: any;

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
  md_body: "",
  parsed_date: now,
  published: "",
  shares_count: 1,
  summary: "summary",
  tags: ["test"],
  title: "how to write a plugin",
}];

const validUser: IParsedUser = {
  bio: "bio",
  custom_css: "",
  display_name: "the.aaron",
  global_id: 4,
  handle: "aaron",
  host: "google.com",
  is_followed: true,
  private: {},
};

const validUserArray: IParsedUser[] = [validUser];

const validBody: Search.ISearchResponse = {
  posts: validParsedPost,
  users: validUserArray,
};

function mountSearchResults() {
  testComponent = mount(
    <HashRouter>
      <div>
        <SearchResults username={"ross"} match={{params: {query: "test"}}}/>
      </div>
    </HashRouter>,
  );
}

describe("SearchResults", () => {

  beforeEach(() => {
    searchRequestStub = sandbox.stub(Search, "SearchRequest" as any);
    searchRequestPromise = new bluebird.Promise((resolve) => {
      resolve(validBody);
    });
    searchRequestStub.returns(searchRequestPromise);
    alertStub = sandbox.stub(SearchResults.prototype, "handleGetPostsErr" as any);
  });

  afterEach(() => {
    sandbox.restore();
    testComponent.unmount();
  });

  it("can mount logged in", (done) => {
    mountSearchResults();
    searchRequestPromise.finally(() => {
      expect(testComponent.exists(".full-search-form")).to.equal(true);
      expect(testComponent.exists(".search-divider")).to.equal(true);
      done();
    });
  });

  it("can mount logged out", (done) => {
    testComponent = mount(
      <HashRouter>
        <div>
          <SearchResults username={""} match={{params: {query: "test"}}}/>
        </div>
      </HashRouter>,
    );
    expect(testComponent.exists(".full-search-form")).to.equal(true);
    expect(testComponent.exists(".search-divider")).to.equal(true);
    done();
  });

  it("can handle query input", (done) => {
    mountSearchResults();
    testComponent.find("[name=\"query\"]")
      .simulate("change", {
        target: {
          name: "query",
          value: "It's a me Mario",
        },
      });
    expect(testComponent.find("SearchResults").state()).to.have.property("query", "It's a me Mario");
    done();
  });

  it("can submit query form", (done) => {
    const submitStub: any = sandbox.stub(SearchResults.prototype, "handleSearchSubmit" as any);
    mountSearchResults();
    testComponent.find(".search-button").first().simulate("click");
    expect(submitStub.called).to.equal(true);
    done();
  });

  it("will display no users text if no users", (done) => {
    searchRequestPromise = new bluebird.Promise((resolve: any) => {
      resolve({posts: validParsedPost, users: []});
    });
    searchRequestStub.returns(searchRequestPromise);
    mountSearchResults();
    searchRequestPromise.finally(() => {
      expect(testComponent.exists("p")).to.equal(true);
      expect(testComponent.text()).to.include("No Users found");
      done();
    });
  });

  it("will display no posts text if no posts", (done) => {
    searchRequestPromise = new bluebird.Promise((resolve: any) => {
      resolve({posts: [], users: validUserArray});
    });
    searchRequestStub.returns(searchRequestPromise);
    mountSearchResults();
    searchRequestPromise.finally(() => {
      expect(testComponent.exists("p")).to.equal(true);
      expect(testComponent.text()).to.include("No Posts found");
      done();
    });
  });

  describe ("dropdown user menu", () => {
    it("won't be displayed without enough users", (done) => {
      mountSearchResults();
      searchRequestPromise.finally(() => {
        expect(testComponent.exists(".user-dropdown")).to.equal(false);
        done();
      });
    });

    it("can be displayed", (done) => {
      searchRequestPromise = new bluebird.Promise((resolve: any) => {
        resolve({posts: validParsedPost, users: [validUser, validUser]});
      });
      searchRequestStub.returns(searchRequestPromise);
      mountSearchResults();
      searchRequestPromise.finally(() => {
        testComponent.find("SearchResults").setState({ display: "inherit" });
        expect(testComponent.exists(".user-dropdown")).to.equal(true);
        done();
      });
    });

    it("can be hidden", (done) => {
      searchRequestPromise = new bluebird.Promise((resolve: any) => {
        resolve({posts: validParsedPost, users: [validUser, validUser]});
      });
      searchRequestStub.returns(searchRequestPromise);
      mountSearchResults();
      searchRequestPromise.finally(() => {
        testComponent.find("SearchResults").setState({ display: "inherit" });
        expect(testComponent.exists(".user-dropdown")).to.equal(true);
        testComponent.find(".user-dropdown").first().simulate("click");
        expect(testComponent.find("SearchResults").state()).to.have.property("display", "none");
        done();
      });
    });
  });
});

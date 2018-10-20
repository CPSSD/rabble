// enzyme.tsx creats and instantiates an adapater, and exports enzyme.
// it is required for every test involving react.

import { configure } from "enzyme";
import * as Adapter from "enzyme-adapter-react-16";

configure({ adapter: new Adapter() });

export * from "enzyme";

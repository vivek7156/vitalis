import { describe, expect, it } from "vitest";
import { validateProfile } from "./validation";

const fields = [["Age", "Age"], ["Gender", "Gender"]];

describe("screening profile validation", () => {
  it("reports missing required fields", () => {
    expect(validateProfile({ Age: "", Gender: "" }, fields)).toEqual({
      Age: "Age is required.",
      Gender: "Gender is required.",
    });
  });

  it("rejects ages outside the supported input range", () => {
    expect(validateProfile({ Age: "13", Gender: "Female" }, fields)).toEqual({
      Age: "Enter an age between 14 and 120.",
    });
  });
});

import { describe, expect, it } from "vitest";
import { cn } from "./utils";

describe("cn", () => {
  it("merges classes", () => {
    expect(cn("text-sm", "text-sm", "font-medium")).toBe("text-sm font-medium");
  });
});


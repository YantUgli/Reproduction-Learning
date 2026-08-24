import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Component from "./solution.jsx";

test("kosong menyapa tamu", () => {
  render(<Component />);
  expect(screen.getByText("Halo, tamu!")).toBeTruthy();
  expect(screen.getByLabelText("nama").value).toBe("");
});

test("mengetik memperbarui sapaan dan nilai input", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.type(screen.getByLabelText("nama"), "Ada");
  expect(screen.getByLabelText("nama").value).toBe("Ada");
  expect(screen.getByText("Halo, Ada!")).toBeTruthy();
});

test("menghapus isi mengembalikan sapaan tamu", async () => {
  const user = userEvent.setup();
  render(<Component />);
  const input = screen.getByLabelText("nama");
  await user.type(input, "Budi");
  await user.clear(input);
  expect(screen.getByText("Halo, tamu!")).toBeTruthy();
});

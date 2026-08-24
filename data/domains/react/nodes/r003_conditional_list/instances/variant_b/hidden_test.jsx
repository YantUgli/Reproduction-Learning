import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Component from "./solution.jsx";

async function invite(user, name) {
  await user.type(screen.getByLabelText("tamu"), name);
  await user.click(screen.getByRole("button", { name: "Undang" }));
}

test("keadaan kosong punya pesannya sendiri", () => {
  render(<Component />);
  expect(screen.getByText("Daftar tamu kosong")).toBeTruthy();
});

test("dua tamu berbeda tampil berurutan", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await invite(user, "ada");
  await invite(user, "budi");
  expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toEqual(["ada", "budi"]);
});

test("nama yang sama tidak digandakan", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await invite(user, "ada");
  await invite(user, "ada");
  expect(screen.getAllByRole("listitem")).toHaveLength(1);
});

test("input dikosongkan & spasi diabaikan", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await invite(user, "ada");
  expect(screen.getByLabelText("tamu").value).toBe("");
  await invite(user, "   ");
  expect(screen.getAllByRole("listitem")).toHaveLength(1);
});

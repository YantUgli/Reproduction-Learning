import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Component from "./solution.jsx";

test("mulai dari nol", () => {
  render(<Component />);
  expect(screen.getByText("Jumlah: 0")).toBeTruthy();
});

test("tiga klik Tambah menaikkan jadi 3", async () => {
  const user = userEvent.setup();
  render(<Component />);
  const tambah = screen.getByRole("button", { name: "Tambah" });
  await user.click(tambah);
  await user.click(tambah);
  await user.click(tambah);
  expect(screen.getByText("Jumlah: 3")).toBeTruthy();
});

test("Reset mengembalikan ke nol", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.click(screen.getByRole("button", { name: "Tambah" }));
  await user.click(screen.getByRole("button", { name: "Reset" }));
  expect(screen.getByText("Jumlah: 0")).toBeTruthy();
});

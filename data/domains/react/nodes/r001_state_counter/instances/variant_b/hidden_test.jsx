import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Component from "./solution.jsx";

test("stok awal 10", () => {
  render(<Component />);
  expect(screen.getByText("Stok: 10")).toBeTruthy();
});

test("dua kali Ambil menurunkan jadi 8", async () => {
  const user = userEvent.setup();
  render(<Component />);
  const ambil = screen.getByRole("button", { name: "Ambil" });
  await user.click(ambil);
  await user.click(ambil);
  expect(screen.getByText("Stok: 8")).toBeTruthy();
});

test("tidak pernah turun di bawah nol", async () => {
  const user = userEvent.setup();
  render(<Component />);
  const ambil = screen.getByRole("button", { name: "Ambil" });
  for (let i = 0; i < 12; i += 1) {
    await user.click(ambil);
  }
  expect(screen.getByText("Stok: 0")).toBeTruthy();
});

test("Isi ulang mengembalikan ke 10", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.click(screen.getByRole("button", { name: "Ambil" }));
  await user.click(screen.getByRole("button", { name: "Isi ulang" }));
  expect(screen.getByText("Stok: 10")).toBeTruthy();
});

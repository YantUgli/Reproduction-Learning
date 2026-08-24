import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Component from "./solution.jsx";

test("kosong menyisakan 20", () => {
  render(<Component />);
  expect(screen.getByText("Sisa: 20")).toBeTruthy();
});

test("sisa berkurang sesuai panjang ketikan", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.type(screen.getByLabelText("pesan"), "halo");
  expect(screen.getByLabelText("pesan").value).toBe("halo");
  expect(screen.getByText("Sisa: 16")).toBeTruthy();
});

test("melebihi batas dipotong di 20 karakter", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.type(screen.getByLabelText("pesan"), "0123456789012345678901234567");
  expect(screen.getByLabelText("pesan").value).toBe("01234567890123456789");
  expect(screen.getByText("Sisa: 0")).toBeTruthy();
});

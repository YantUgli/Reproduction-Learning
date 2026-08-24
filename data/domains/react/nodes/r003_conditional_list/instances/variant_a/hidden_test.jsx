import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Component from "./solution.jsx";

test("keadaan kosong punya pesannya sendiri", () => {
  render(<Component />);
  expect(screen.getByText("Belum ada tugas")).toBeTruthy();
  expect(screen.queryAllByRole("listitem")).toHaveLength(0);
});

test("menambah dua tugas menampilkan dua item", async () => {
  const user = userEvent.setup();
  render(<Component />);
  const input = screen.getByLabelText("tugas");
  const tambah = screen.getByRole("button", { name: "Tambah" });

  await user.type(input, "belajar");
  await user.click(tambah);
  await user.type(input, "istirahat");
  await user.click(tambah);

  const items = screen.getAllByRole("listitem").map((li) => li.textContent);
  expect(items).toEqual(["belajar", "istirahat"]);
  expect(screen.queryByText("Belum ada tugas")).toBeNull();
});

test("input dikosongkan setelah menambah", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.type(screen.getByLabelText("tugas"), "menulis");
  await user.click(screen.getByRole("button", { name: "Tambah" }));
  expect(screen.getByLabelText("tugas").value).toBe("");
});

test("input kosong tidak menambah apa pun", async () => {
  const user = userEvent.setup();
  render(<Component />);
  await user.type(screen.getByLabelText("tugas"), "   ");
  await user.click(screen.getByRole("button", { name: "Tambah" }));
  expect(screen.getByText("Belum ada tugas")).toBeTruthy();
});

import "./globals.css";
import AreaSwitch from "./components/AreaSwitch";
import { ConfirmProvider } from "./components/ui/ConfirmProvider";

export const metadata = {
  title: "Reproduction Learning Engine",
  description: "Ukuran belajar: reproduce-without-AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body className="min-h-screen bg-canvas text-fg antialiased">
        <ConfirmProvider>
          {/* Frame orientasi persisten (§5/§8): Forge · Library · Authoring. */}
          <AreaSwitch />
          <div className="px-4 py-8 sm:px-8">{children}</div>
        </ConfirmProvider>
      </body>
    </html>
  );
}

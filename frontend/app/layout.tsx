import "./globals.css";

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
      <body className="min-h-screen bg-canvas px-4 py-8 text-fg antialiased sm:px-8">
        {children}
      </body>
    </html>
  );
}

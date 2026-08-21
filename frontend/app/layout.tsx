export const metadata = {
  title: "Reproduction Learning Engine",
  description: "M0 scaffolding",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          margin: 0,
          padding: "2rem",
        }}
      >
        {children}
      </body>
    </html>
  );
}

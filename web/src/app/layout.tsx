import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Inventory AI",
  description: "Stock and warehouse operations — portfolio MVP skeleton",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

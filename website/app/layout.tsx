import { ClerkProvider, Show, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sjursen Digital — Self-hosted business software",
  description:
    "Sjursen Digital builds self-hostable business software. One gateway, your infrastructure, your data.",
  icons: { icon: "/favicon.png" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <ClerkProvider appearance={{ baseTheme: dark }}>
          <header className="site-header">
            <div className="header-inner">
              <a className="brand" href="/">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img className="brand-logo" src="/logo-white.png" alt="Sjursen Digital logo" />
                <span className="brand-name">Sjursen Digital</span>
              </a>

              <nav className="site-nav">
                <a href="/#products">Products</a>
                <a href="/#how-it-works">How it works</a>
                <a href="/#download">Download</a>
              </nav>

              <div className="header-actions">
                <Show when="signed-out">
                  <SignInButton mode="modal">
                    <button className="auth-btn">Sign in</button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button className="auth-btn primary">Create account</button>
                  </SignUpButton>
                </Show>
                <Show when="signed-in">
                  <a className="auth-btn" href="/portal">
                    My account
                  </a>
                  <UserButton />
                </Show>
              </div>
            </div>
          </header>

          <main className="flex-1">{children}</main>

          <footer className="site-footer">
            <div className="footer-inner">
              <div className="footer-brand">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img className="footer-logo" src="/logo-white.png" alt="" />
                <div>
                  <div className="footer-name">Sjursen Digital</div>
                  <div className="footer-sub">Self-hosted business software</div>
                </div>
              </div>
              <div className="footer-meta">
                <span>Bergen, Norway</span>
                <span className="footer-dot">·</span>
                <a href="mailto:contact@sjursendigital.no">contact@sjursendigital.no</a>
              </div>
            </div>
          </footer>
        </ClerkProvider>
      </body>
    </html>
  );
}

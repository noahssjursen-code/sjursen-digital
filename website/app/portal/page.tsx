import { currentUser } from "@clerk/nextjs/server";

export const metadata = {
  title: "My account — Sjursen Digital",
};

export default async function PortalPage() {
  const user = await currentUser();
  const email = user?.primaryEmailAddress?.emailAddress ?? "";
  const name = user?.fullName || user?.firstName || email;

  return (
    <section className="portal">
      <div className="section-inner">
        <div className="portal-head">
          <div>
            <h1 className="section-title">My account</h1>
            <p className="portal-sub">
              Signed in as <strong>{name}</strong>
              {email && name !== email ? <> ({email})</> : null}
            </p>
          </div>
          {user?.imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img className="portal-avatar" src={user.imageUrl} alt="" />
          ) : null}
        </div>

        <div className="portal-grid">
          <div className="portal-card">
            <div className="portal-card-tag">Coming soon</div>
            <h3>Workspace</h3>
            <p>
              Your account works on its own for personal projects and homelabs. Running with a
              team? Create a shared workspace and invite others to manage the subscription
              together.
            </p>
          </div>

          <div className="portal-card">
            <div className="portal-card-tag">Coming soon</div>
            <h3>License &amp; downloads</h3>
            <p>
              Your Gateway license key and the Docker image download will live here once the first
              module reaches a stable release.
            </p>
          </div>

          <div className="portal-card">
            <div className="portal-card-tag">Coming soon</div>
            <h3>Billing</h3>
            <p>
              Subscription plan, invoices, and payment details. Billing opens together with
              licensing.
            </p>
          </div>

          <div className="portal-card">
            <h3>Profile &amp; security</h3>
            <p>
              Manage your email addresses, connected accounts, and sessions from the avatar menu in
              the top-right corner.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

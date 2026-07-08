export default function Home() {
  return (
    <>
      {/* ============================================================ HERO */}
      <section className="hero">
        <div className="hero-glow" aria-hidden="true"></div>
        <div className="section-inner">
          <h1 className="hero-title">
            Business software that runs on <span className="hero-accent">your infrastructure.</span>
          </h1>
          <p className="hero-lede">
            Sjursen Digital builds a suite of operational tools delivered as one self-hosted
            gateway. One container, every app, your servers. Employee data, logs, and operations
            never leave your network.
          </p>
          <div className="hero-actions">
            <a className="cta primary" href="#download">
              Get the Gateway
            </a>
            <a className="cta secondary" href="#how-it-works">
              How it works
            </a>
          </div>
        </div>
      </section>

      {/* ============================================================ VALUE PROPS */}
      <section className="values">
        <div className="section-inner">
          <div className="value-grid">
            <div className="value">
              <h3>Your data stays yours</h3>
              <p>
                Everything runs inside your network. No third-party processors, no data processing
                agreements for employee data, no surprise subprocessor lists. Compliance becomes
                simple when nothing leaves the building.
              </p>
            </div>
            <div className="value">
              <h3>One container, the whole suite</h3>
              <p>
                The Gateway is a single deployment that bundles every Sjursen Digital app. Enable
                the modules you pay for, ignore the rest. Adding an app later is a license change,
                not a new infrastructure project.
              </p>
            </div>
            <div className="value">
              <h3>Your identity provider</h3>
              <p>
                Connect the Gateway to your own Microsoft Entra ID, Google Workspace, or any OIDC
                provider. Your employees sign in with the accounts they already have — we are never
                in that loop.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ HOW IT WORKS */}
      <section className="how" id="how-it-works">
        <div className="section-inner">
          <h2 className="section-title">How it works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-num">1</div>
              <h3>Create an account</h3>
              <p>
                For yourself or your whole company — one account manages your subscription and
                license. Nothing else lives in our cloud.
              </p>
            </div>
            <div className="step">
              <div className="step-num">2</div>
              <h3>Deploy the Gateway</h3>
              <p>
                Download a single Docker image and run it on a VPS or on-premise hardware. Your
                license key unlocks the modules in your plan.
              </p>
            </div>
            <div className="step">
              <div className="step-num">3</div>
              <h3>Connect your sign-in</h3>
              <p>
                Solo? You're ready to go. Running with a team, point the Gateway at your identity
                provider and everyone signs in with the work accounts they already have — every
                action traceable to a person.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ PRODUCTS */}
      <section className="products" id="products">
        <div className="section-inner">
          <h2 className="section-title">The suite</h2>
          <p className="section-lede">
            The first modules are in active development. Each one targets an operational problem
            that teams currently solve with spreadsheets, fragile scripts, or expensive per-seat
            SaaS.
          </p>
          <div className="product-grid">
            <div className="product">
              <div className="product-tag">In development</div>
              <h3>Event monitoring &amp; decisions</h3>
              <p>
                Stream logs and sensor data into a stateful engine that watches thresholds, detects
                silence, and escalates with structured decisions your code can act on.
              </p>
            </div>
            <div className="product">
              <div className="product-tag">In development</div>
              <h3>Physical asset tracking</h3>
              <p>
                QR codes on equipment, scanned from any phone. Maintenance logs, usage history, and
                certification checks — an audit trail your safety inspector will love.
              </p>
            </div>
            <div className="product">
              <div className="product-tag">Planned</div>
              <h3>More to come</h3>
              <p>
                The Gateway is built to grow. New modules ship into the same container you already
                run — enable them with a license update.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ DOWNLOAD */}
      <section className="download" id="download">
        <div className="section-inner">
          <div className="download-box">
            <h2 className="section-title">Download the Gateway</h2>
            <p>
              The Gateway is in active development and not yet available for public download.
              Accounts, licensing, and payments open together with the first stable module.
            </p>
            <p className="download-note">
              Interested in early access for your company? Reach out:{" "}
              <a href="mailto:contact@sjursendigital.no">contact@sjursendigital.no</a>
            </p>
          </div>
        </div>
      </section>
    </>
  );
}

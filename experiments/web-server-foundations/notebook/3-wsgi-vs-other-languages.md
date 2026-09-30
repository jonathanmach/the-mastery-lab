This architectural difference divides modern server-side programming into two main camps: **Self-Hosted Application Servers** (like Go) and **Gateway/App-Server Architecture** (like Python).

---

### Languages Like Go (Self-Hosted Servers)

These languages include built-in or native production-ready HTTP engines and asynchronous/concurrent runtimes. Instead of relying on an external gateway bridge, the application compiles or executes as its own standalone web server listening directly on a TCP port.

| Language | Primary Web Mechanism | How It Works |
| --- | --- | --- |
| **Node.js / JavaScript** | Built-in `http` module | Node pioneered this modern pattern. Its single-threaded event loop binds directly to sockets using `http.createServer()`. Express, Fastify, and NestJS run directly inside the process without a gateway wrapper. |
| **Rust** | Async engines (`tokio`, `hyper`, `axum`, `actix-web`) | Rust provides direct socket control and high-performance asynchronous runtimes. Applications compile into standalone native binaries with integrated multi-threaded servers. |
| **C# / .NET** | **Kestrel** (built-in ASP.NET Core engine) | Historically, .NET required IIS (similar to WSGI). With modern .NET Core / .NET 6+, Microsoft replaced that model with Kestrel—a cross-platform, high-throughput built-in web server. |
| **Java (Modern)** | Embedded engines (Netty, Undertow, embedded Tomcat) | While traditional Java used servlet containers (like standalone Tomcat), modern frameworks like **Spring Boot**, **Quarkus**, and **Micronaut** package the web engine directly into an executable `.jar`. |
| **Elixir / Erlang** | **Bandit** / **Cowboy** (BEAM runtime) | The BEAM runtime treats network connections as lightweight isolated processes. Libraries like Bandit integrate directly into Elixir's `Plug` specification without external server daemons. |

---

### Languages Like Python (Gateway / Application Server Model)

These languages traditionally separate the **web server** (which handles network sockets, workers, and process management) from the **application framework** (which handles business logic and routing). A standardized interface sits in between.

| Language | Standard Specification | Common App Servers & Implementations |
| --- | --- | --- |
| **Ruby** | **Rack** | Rack is Ruby’s direct equivalent of WSGI. Frameworks like **Rails** and **Sinatra** implement the Rack interface, while application servers like **Puma**, **Unicorn**, or **Falcon** manage worker processes and HTTP connections. |
| **Python** | **WSGI** & **ASGI** | WSGI handles synchronous frameworks (Django, Flask) via servers like **Gunicorn** and **uWSGI**. ASGI extends this to asynchronous code (FastAPI, Starlette) via servers like **Uvicorn** and **Hypercorn**. |
| **Perl** | **PSGI** | Perl adopted the Python/Ruby model through PSGI. Servers like **Starman** run PSGI-compatible frameworks like **Dancer** and **Mojolicious**. |
| **PHP** | **SAPI / FastCGI** | PHP historically bypassed raw socket handling entirely. Instead, web servers like Apache (`mod_php`) or Nginx talk to **PHP-FPM** (FastCGI Process Manager) over FastCGI, booting and tearing down script state per request. |
| **Java (Legacy)** | **Jakarta / Java Servlet API** | The classic enterprise Java model: WAR files are deployed to a standalone application server or servlet container (e.g., Apache Tomcat, WildFly, GlassFish), which controls process lifecycles. |

---

### Why the Divide Exists

* **Threading & Concurrency Models:** Languages like Python and Ruby have a Global Interpreter Lock (GIL) and rely on pre-forking multi-process supervisors (like Gunicorn or Puma) to utilize multiple CPU cores safely.
* **Socket & Runtime Design:** Languages like Go (Goroutines), Node.js (Event Loop), and Rust (Tokio) handle thousands of concurrent non-blocking socket connections natively within a single running process, making a dedicated external gateway server redundant.

*(Note: In production, even self-hosted languages like Go and Node.js often sit behind a reverse proxy like Nginx, Caddy, or Cloudflare for TLS termination, caching, and rate limiting—but the application itself communicates via standard HTTP rather than a language-specific gateway protocol like WSGI).*
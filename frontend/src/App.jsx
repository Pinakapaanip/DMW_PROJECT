import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import { apiRequest, displayName, errorMessage, readList, recordId } from "./api.js";

const iconPaths = {
  home: <><path d="m3 10 9-7 9 7" /><path d="M5 9v11h14V9M9 20v-6h6v6" /></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="10" cy="7" r="4" /><path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></>,
  book: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" /></>,
  plus: <><path d="M12 5v14M5 12h14" /></>,
  arrow: <><path d="M7 17 17 7M7 7h10v10" /></>,
  spark: <><path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-2-5.8L4 11l6-2.2L12 3Z" /><path d="m19 14 1.1 2.9L23 18l-2.9 1.1L19 22l-1.1-2.9L15 18l2.9-1.1L19 14Z" /></>,
  search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></>,
  chevron: <path d="m9 18 6-6-6-6" />,
  logout: <><path d="M10 17l5-5-5-5M15 12H3" /><path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  heart: <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z" />,
  message: <><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8A8.5 8.5 0 0 1 8.7 3.9a8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z" /></>,
  bookmark: <><path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-4-6 4V4.5Z" /></>,
  settings: <><circle cx="12" cy="12" r="3" /><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a8 8 0 0 1-1.6.9l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.6-.9l-1.7.7-1.4-2.4 1.4-1.1a7 7 0 0 1 0-1.9l-1.4-1.1 1.4-2.4 1.7.7a8 8 0 0 1 1.6-.9l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.6.9l1.7-.7 1.4 2.4-1.4 1.1a7 7 0 0 1-.1 1.8Z" transform="translate(-2 -2)" /></>,
};

function Icon({ name, size = 19 }) {
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {iconPaths[name]}
    </svg>
  );
}

function getStoredToken() {
  return window.sessionStorage.getItem("commons_token");
}

function App() {
  const [token, setToken] = useState(getStoredToken);
  const [user, setUser] = useState(null);
  const [authStatus, setAuthStatus] = useState(token ? "checking" : "signed-out");
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    if (!token) {
      setAuthStatus("signed-out");
      setUser(null);
      return;
    }
    let active = true;
    apiRequest("/auth/me", { token })
      .then((result) => {
        if (!active) return;
        setUser(result?.user ?? result);
        setAuthStatus("signed-in");
        setAuthError("");
      })
      .catch((error) => {
        if (!active) return;
        setAuthError(errorMessage(error));
        if (error.status === 401) {
          window.sessionStorage.removeItem("commons_token");
          setToken(null);
        } else {
          setAuthStatus("unavailable");
        }
      });
    return () => { active = false; };
  }, [token]);

  const signIn = useCallback((nextToken, nextUser) => {
    window.sessionStorage.setItem("commons_token", nextToken);
    setToken(nextToken);
    setUser(nextUser ?? null);
    setAuthStatus("signed-in");
    setAuthError("");
  }, []);

  const signOut = useCallback(() => {
    window.sessionStorage.removeItem("commons_token");
    setToken(null);
    setUser(null);
    setAuthStatus("signed-out");
  }, []);

  const auth = useMemo(() => ({
    token, user, authStatus, authError, signIn, signOut,
    setUser,
  }), [token, user, authStatus, authError, signIn, signOut]);

  return (
    <Routes>
      <Route path="/login" element={authStatus === "checking" ? <LoadingPage /> : <AuthPage mode="login" auth={auth} />} />
      <Route path="/register" element={authStatus === "checking" ? <LoadingPage /> : <AuthPage mode="register" auth={auth} />} />
      <Route element={<RequireAuth auth={auth} />}>
        <Route element={<AppShell auth={auth} />}>
          <Route index element={<Navigate to="/feed" replace />} />
          <Route path="/feed" element={<FeedPage auth={auth} />} />
          <Route path="/members" element={<MembersPage auth={auth} />} />
          <Route path="/profile" element={<ProfilePage auth={auth} />} />
          <Route path="/profile/:userId" element={<ProfilePage auth={auth} />} />
          <Route path="/library" element={<LibraryPage auth={auth} />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

function RequireAuth({ auth }) {
  const location = useLocation();
  if (auth.authStatus === "checking") return <LoadingPage />;
  if (auth.authStatus === "unavailable") {
    return <AuthPage mode="login" auth={auth} initialError={auth.authError} />;
  }
  return auth.authStatus === "signed-in"
    ? <Outlet />
    : <Navigate to="/login" state={{ from: location }} replace />;
}

function AuthPage({ mode, auth, initialError = "" }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isRegister = mode === "register";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initialError);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "student" });

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (isRegister) {
        const registered = await apiRequest("/auth/register", {
          method: "POST",
          body: { name: form.name.trim(), email: form.email.trim(), password: form.password, role: form.role },
        });
        const returnedToken = registered?.access_token ?? registered?.token;
        if (returnedToken) {
          auth.signIn(returnedToken, registered.user);
          navigate("/", { replace: true });
          return;
        }
      }
      const result = await apiRequest("/auth/login", {
        method: "POST",
        body: { email: form.email.trim(), password: form.password },
      });
      const accessToken = result?.access_token ?? result?.token;
      if (!accessToken) throw new Error("The login response did not include an access token.");
      auth.signIn(accessToken, result.user);
      const destination = location.state?.from?.pathname || "/feed";
      navigate(destination, { replace: true });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-story">
        <Link to="/login" className="brand brand-on-dark">
          <span className="brand-mark"><span /></span>
          <span>commons<span className="brand-period">.</span></span>
        </Link>
        <div className="story-copy">
          <p className="eyebrow eyebrow-light">CHANAKYA RESEARCH COMMONS</p>
          <h1>Good research<br />moves <em>together.</em></h1>
          <p className="story-subtitle">A home for the questions, ideas, and people shaping what comes next.</p>
        </div>
        <div className="story-foot">
          <div className="orbit-art" aria-hidden="true"><i /><i /><i /><b>c</b></div>
          <span>Curiosity, connected.</span>
          <span className="story-year">CU · 2026</span>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-topline">
          <span>{isRegister ? "YOUR NEXT CHAPTER" : "WELCOME BACK"}</span>
          <span className="status-dot" /> PRIVATE UNIVERSITY NETWORK
        </div>
        <div className="auth-form-wrap">
          <p className="eyebrow">{isRegister ? "JOIN THE COMMUNITY" : "YOUR RESEARCH SPACE"}</p>
          <h2>{isRegister ? "Create your account" : "Sign in to Commons"}</h2>
          <p className="muted">{isRegister ? "Bring your questions. Find your people." : "Pick up where your curiosity left off."}</p>
          <form onSubmit={submit} className="form-stack">
            {isRegister && (
              <>
                <label className="field-label">Full name
                  <input autoComplete="name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="How should we address you?" />
                </label>
                <label className="field-label">I’m joining as
                  <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                    <option value="student">Student</option>
                    <option value="faculty">Faculty</option>
                    <option value="researcher">Researcher</option>
                  </select>
                </label>
              </>
            )}
            <label className="field-label">University email
              <input type="email" autoComplete="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@chanakyauniversity.edu.in" />
            </label>
            <label className="field-label">Password
              <input type="password" autoComplete={isRegister ? "new-password" : "current-password"} minLength={8} required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="At least 8 characters" />
            </label>
            {error && <ErrorBanner message={error} />}
            <button type="submit" className="button button-primary button-wide" disabled={busy}>
              {busy ? "One moment…" : isRegister ? "Create account" : "Sign in"}
              {!busy && <Icon name="arrow" size={17} />}
            </button>
          </form>
          <div className="auth-switch">
            {isRegister ? "Already part of Commons?" : "New to Commons?"}
            {" "}<Link to={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create an account"}</Link>
          </div>
        </div>
        <p className="auth-legal">By continuing, you agree to use this space with care and academic integrity.</p>
      </section>
    </main>
  );
}

function AppShell({ auth }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const name = displayName(auth.user);
  const initials = name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  const links = [
    { to: "/feed", icon: "home", label: "Research feed" },
    { to: "/members", icon: "users", label: "People" },
    { to: "/library", icon: "book", label: "My library" },
  ];
  return (
    <div className="app-frame">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <Link to="/feed" className="brand">
          <span className="brand-mark"><span /></span><span>commons<span className="brand-period">.</span></span>
        </Link>
        <div className="workspace-label">YOUR WORKSPACE <span>CU</span></div>
        <nav className="main-nav" aria-label="Main navigation">
          {links.map(({ to, icon, label }) => (
            <NavLink key={to} to={to} onClick={() => setMenuOpen(false)} className={({ isActive }) => `nav-link ${isActive ? "nav-active" : ""}`}>
              <Icon name={icon} /><span>{label}</span>{to === "/feed" && <span className="nav-indicator" />}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-tip">
            <div className="tip-icon"><Icon name="spark" size={17} /></div>
            <strong>Ideas grow here.</strong>
            <span>Share a question, a finding, or a fresh perspective.</span>
            <Link to="/feed" onClick={() => setMenuOpen(false)}>Go to your feed <Icon name="arrow" size={14} /></Link>
          </div>
          <Link to="/profile" className="account-row">
            <Avatar name={name} initials={initials} size="small" />
            <span className="account-copy"><strong>{name}</strong><small>{auth.user?.role || "Community member"}</small></span>
            <Icon name="chevron" size={16} />
          </Link>
          <button type="button" className="logout-button" onClick={auth.signOut}><Icon name="logout" size={16} /> Sign out</button>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <button type="button" className="mobile-menu" aria-label="Toggle navigation" onClick={() => setMenuOpen(!menuOpen)}><Icon name="menu" /></button>
          <div className="breadcrumb"><span>Chanakya University</span><Icon name="chevron" size={14} /><strong>Research Commons</strong></div>
          <div className="topbar-right">
            <div className="network-pill"><span className="status-dot" /> COMMUNITY SPACE</div>
            <Link to="/profile" className="top-avatar" title="Your profile"><Avatar name={name} initials={initials} size="tiny" /></Link>
          </div>
        </header>
        <main className="page-content"><Outlet /></main>
        <footer className="app-footer"><span>Made for people who ask better questions.</span><span>CHANAKYA RESEARCH COMMONS · 2026</span></footer>
      </div>
    </div>
  );
}

function PageHeading({ kicker, title, description, action }) {
  return (
    <div className="page-heading">
      <div><p className="eyebrow">{kicker}</p><h1>{title}</h1>{description && <p className="page-description">{description}</p>}</div>
      {action}
    </div>
  );
}

function FeedPage({ auth }) {
  const [posts, setPosts] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true;
    setStatus("loading");
    apiRequest("/feed", { token: auth.token })
      .then((data) => {
        if (!active) return;
        setPosts(readList(data, "posts"));
        setStatus("ready");
      })
      .catch((e) => { if (active) { setError(errorMessage(e)); setStatus("error"); } });
    return () => { active = false; };
  }, [auth.token, refresh]);
  return (
    <>
      <div className="feed-intro">
        <div>
          <p className="eyebrow">{new Intl.DateTimeFormat("en", { weekday: "long", month: "long", day: "numeric", year: "numeric" }).format(new Date()).toUpperCase()} <span className="tiny-sun">✳</span> YOUR COMMUNITY, IN MOTION</p>
          <h1>Research is better<br /><em>when it’s shared.</em></h1>
          <p className="page-description">A thoughtful space for ideas in progress, questions worth asking, and discoveries worth passing on.</p>
        </div>
        <div className="feed-stamp" aria-hidden="true"><div className="stamp-lines"><span>THINK</span><span>·</span><span>TOGETHER</span></div><b>c.</b><small>CU RESEARCH COMMONS</small></div>
      </div>
      <div className="feed-layout">
        <section className="feed-main">
          <Composer auth={auth} onCreated={() => setRefresh((n) => n + 1)} />
          <div className="section-title-row"><div><p className="eyebrow">THE CONVERSATION</p><h2>Latest from your network</h2></div><span className="live-label"><i /> LIVE FEED</span></div>
          {status === "loading" && <LoadingCard label="Finding the latest from your network…" />}
          {status === "error" && <ErrorPanel message={error} onRetry={() => setRefresh((n) => n + 1)} />}
          {status === "ready" && posts.length === 0 && <EmptyPanel icon="message" title="The conversation starts with you." body="No posts in your feed just yet. Share a question or finding to get things moving." />}
          {status === "ready" && posts.map((post, index) => <PostCard key={recordId(post) ?? index} post={post} auth={auth} onChanged={() => setRefresh((n) => n + 1)} />)}
        </section>
        <aside className="feed-rail">
          <div className="rail-card community-card">
            <div className="rail-kicker"><span className="status-dot" /> YOUR COMMUNITY</div>
            <div className="community-art" aria-hidden="true"><span className="art-ring ring-one" /><span className="art-ring ring-two" /><span className="art-dot dot-one" /><span className="art-dot dot-two" /><span className="art-core">c.</span></div>
            <h3>A place for ideas<br />to find each other.</h3>
            <p>Follow researchers, share work in progress, and make your next good question count.</p>
            <Link className="text-link" to="/members">Meet the community <Icon name="arrow" size={15} /></Link>
          </div>
          <div className="rail-note"><span className="note-mark">“</span><p>Big discoveries often begin as small conversations.</p><span>THE COMMONS PRINCIPLE</span></div>
        </aside>
      </div>
    </>
  );
}

function Composer({ auth, onCreated }) {
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const name = displayName(auth.user);
  async function submit(event) {
    event.preventDefault();
    if (!body.trim()) return;
    setBusy(true);
    setError("");
    try {
      await apiRequest("/posts", { method: "POST", token: auth.token, body: { body: body.trim(), tags: [] } });
      setBody("");
      onCreated();
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return (
    <form className="composer-card" onSubmit={submit}>
      <div className="composer-top"><Avatar name={name} /><label htmlFor="post-body">What’s on your research mind?</label><span className="compose-private"><span /> COMMUNITY</span></div>
      <textarea id="post-body" value={body} onChange={(e) => setBody(e.target.value)} maxLength={5000} placeholder="Share an idea, ask a question, or tell us what you’re exploring…" rows={3} />
      {error && <ErrorBanner message={error} />}
      <div className="composer-bottom"><span>Thoughtful conversations make stronger research.</span><button className="button button-primary" disabled={busy || !body.trim()}><Icon name="plus" size={16} /> {busy ? "Publishing…" : "Share with community"}</button></div>
    </form>
  );
}

function PostCard({ post, auth, onChanged }) {
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const author = post.author || post.user || {};
  const authorName = displayName(author);
  const body = post.body ?? post.content ?? "";
  const postId = recordId(post);
  const created = post.created_at || post.createdAt;
  const commentList = Array.isArray(post.comments) ? post.comments : [];
  async function upvote() {
    if (!postId) { setError("This post does not include an ID, so it cannot be upvoted."); return; }
    setBusy(true);
    setError("");
    try { await apiRequest(`/posts/${encodeURIComponent(postId)}/upvote`, { method: "POST", token: auth.token }); onChanged(); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function addComment(event) {
    event.preventDefault();
    if (!comment.trim() || !postId) return;
    setBusy(true);
    setError("");
    try {
      await apiRequest(`/posts/${encodeURIComponent(postId)}/comments`, { method: "POST", token: auth.token, body: { body: comment.trim() } });
      setComment("");
      onChanged();
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return (
    <article className="post-card">
      <div className="post-head"><Avatar name={authorName} /><div className="post-author"><strong>{authorName}</strong><span>{[author.department, author.role].filter(Boolean).join(" · ") || "Research community"}</span></div><time>{formatDate(created)}</time></div>
      <p className="post-body">{body || "This post has no text content."}</p>
      {Array.isArray(post.tags) && post.tags.length > 0 && <div className="tag-row">{post.tags.map((tag) => <span key={typeof tag === "string" ? tag : tag.name}>#{typeof tag === "string" ? tag : tag.name}</span>)}</div>}
      {error && <ErrorBanner message={error} />}
      <div className="post-actions">
        <button type="button" className="post-action" onClick={upvote} disabled={busy}><Icon name="heart" size={17} /> <span>{post.upvotes_count ?? post.upvote_count ?? post.upvotes?.length ?? 0}</span></button>
        <button type="button" className="post-action" onClick={() => setShowComment(!showComment)}><Icon name="message" size={17} /> <span>{post.comments_count ?? commentList.length} comments</span></button>
        {post.paper && <span className="post-paper"><Icon name="bookmark" size={15} /> Research attached</span>}
      </div>
      {showComment && (
        <div className="comment-area">
          {commentList.map((item, index) => <div className="comment-item" key={recordId(item) ?? index}><Avatar name={displayName(item.author || item.user || {})} size="tiny" /><p><strong>{displayName(item.author || item.user || {})}</strong> {item.body ?? item.content}</p></div>)}
          <form className="comment-form" onSubmit={addComment}><input aria-label="Write a comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add a thoughtful comment…" /><button type="submit" className="icon-button" disabled={busy || !comment.trim()} aria-label="Post comment"><Icon name="arrow" size={17} /></button></form>
        </div>
      )}
    </article>
  );
}

function MembersPage({ auth }) {
  const [members, setMembers] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true;
    apiRequest("/users", { token: auth.token })
      .then((result) => { if (active) { setMembers(readList(result, "users")); setStatus("ready"); } })
      .catch((e) => { if (active) { setError(errorMessage(e)); setStatus("error"); } });
    return () => { active = false; };
  }, [auth.token, refresh]);
  return (
    <>
      <PageHeading kicker="PEOPLE & PERSPECTIVES" title={<>Research, at its heart,<br /><em>is a human thing.</em></>} description="Meet the people asking good questions across Chanakya University." />
      <section className="directory-panel">
        <div className="directory-top"><div><p className="eyebrow">THE DIRECTORY</p><h2>People in the Commons</h2></div><span className="member-count">{status === "ready" ? `${members.length} ${members.length === 1 ? "MEMBER" : "MEMBERS"}` : "COMMUNITY"}</span></div>
        {status === "loading" && <LoadingCard label="Finding researchers…" />}
        {status === "error" && <ErrorPanel message={error} onRetry={() => setRefresh((n) => n + 1)} />}
        {status === "ready" && members.length === 0 && <EmptyPanel icon="users" title="The directory is ready to grow." body="There are no members to show yet. Once the community joins, you’ll find their research interests here." />}
        {status === "ready" && members.length > 0 && <div className="member-grid">{members.map((member, index) => <MemberCard key={recordId(member) ?? index} member={member} auth={auth} />)}</div>}
      </section>
    </>
  );
}

function MemberCard({ member, auth }) {
  const [following, setFollowing] = useState(Boolean(member.is_following ?? member.following));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const id = recordId(member);
  const name = displayName(member);
  async function toggleFollow() {
    if (!id) { setError("This profile does not include an ID, so it cannot be followed."); return; }
    setBusy(true);
    setError("");
    try {
      await apiRequest(`/users/${encodeURIComponent(id)}/follow`, { method: following ? "DELETE" : "POST", token: auth.token });
      setFollowing(!following);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return (
    <article className="member-card">
      <div className="member-card-top"><Avatar name={name} size="large" /><button className={`follow-button ${following ? "is-following" : ""}`} onClick={toggleFollow} disabled={busy}>{busy ? "…" : following ? "Following" : "Follow"}</button></div>
      <Link to={`/profile/${encodeURIComponent(id ?? "")}`} className="member-name">{name}<Icon name="arrow" size={14} /></Link>
      <p className="member-meta">{member.department || member.role || "Chanakya University"}</p>
      {member.bio && <p className="member-bio">{member.bio}</p>}
      {Array.isArray(member.interests) && <div className="tag-row">{member.interests.slice(0, 3).map((interest) => <span key={interest}>#{interest}</span>)}</div>}
      {error && <ErrorBanner message={error} />}
    </article>
  );
}

function ProfilePage({ auth }) {
  const { userId } = useParams();
  const isOwn = !userId || String(userId) === String(recordId(auth.user));
  const [profile, setProfile] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true;
    setStatus("loading");
    apiRequest(isOwn ? "/users/me" : `/users/${encodeURIComponent(userId)}`, { token: auth.token })
      .then((result) => { if (active) { setProfile(result?.user ?? result); setStatus("ready"); } })
      .catch((e) => { if (active) { setError(errorMessage(e)); setStatus("error"); } });
    return () => { active = false; };
  }, [auth.token, userId, isOwn, refresh]);

  async function saveProfile(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const formData = new FormData(event.currentTarget);
    const interests = String(formData.get("interests") || "").split(",").map((item) => item.trim()).filter(Boolean);
    try {
      const result = await apiRequest("/users/me", {
        method: "PUT", token: auth.token,
        body: { full_name: formData.get("full_name"), department: formData.get("department"), bio: formData.get("bio"), interests },
      });
      setProfile(result?.user ?? result);
      auth.setUser(result?.user ?? result);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2600);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  const name = displayName(profile || auth.user);
  if (status === "loading") return <LoadingPage />;
  return (
    <>
      <PageHeading kicker={isOwn ? "YOUR RESEARCH IDENTITY" : "A MEMBER OF THE COMMONS"} title={isOwn ? <>Your work, your<br /><em>point of view.</em></> : <>Meet a fellow<br /><em>curious mind.</em></>} description={isOwn ? "Tell the community what you’re exploring and what matters to you." : "A researcher in the Chanakya University community."} />
      {status === "error" ? <ErrorPanel message={error} onRetry={() => setRefresh((n) => n + 1)} /> : (
        <section className="profile-layout">
          <div className="profile-card">
            <div className="profile-cover"><span className="cover-orbit orbit-a" /><span className="cover-orbit orbit-b" /><span className="cover-signature">C<span>.</span>U</span></div>
            <div className="profile-identity"><Avatar name={name} size="profile" /><div><h2>{name}</h2><p>{profile?.department || profile?.role || "Chanakya University"}</p></div></div>
            {!isOwn && <FollowProfileButton userId={userId} following={Boolean(profile?.is_following ?? profile?.following)} token={auth.token} />}
            <div className="profile-details"><div><span className="detail-label">ABOUT</span><p>{profile?.bio || "This researcher hasn’t added a bio yet."}</p></div><div><span className="detail-label">RESEARCH INTERESTS</span><div className="tag-row">{Array.isArray(profile?.interests) && profile.interests.length ? profile.interests.map((interest) => <span key={interest}>#{interest}</span>) : <span className="empty-interest">Interests haven’t been added yet.</span>}</div></div></div>
          </div>
          {isOwn && <form className="edit-profile-card" onSubmit={saveProfile}>
            <div className="section-title-row"><div><p className="eyebrow">MAKE IT YOURS</p><h2>Edit your profile</h2></div><span className="profile-edit-icon"><Icon name="settings" /></span></div>
            <label className="field-label">Full name<input name="full_name" defaultValue={profile?.full_name || profile?.name || ""} required /></label>
            <label className="field-label">Department<input name="department" defaultValue={profile?.department || ""} placeholder="e.g. Computer Science" /></label>
            <label className="field-label">A little about your work<textarea name="bio" defaultValue={profile?.bio || ""} rows={3} maxLength={1000} placeholder="What are you curious about right now?" /></label>
            <label className="field-label">Research interests<span className="input-hint">Separate each interest with a comma.</span><input name="interests" defaultValue={Array.isArray(profile?.interests) ? profile.interests.join(", ") : ""} placeholder="Climate, machine learning, public health…" /></label>
            {error && <ErrorBanner message={error} />}
            <div className="profile-save-row"><span className="save-confirmation">{saved ? "Profile saved." : "Only share what you’re comfortable sharing."}</span><button className="button button-primary" disabled={busy}>{busy ? "Saving…" : "Save profile"} <Icon name="arrow" size={16} /></button></div>
          </form>}
        </section>
      )}
    </>
  );
}

function FollowProfileButton({ userId, following: initial, token }) {
  const [following, setFollowing] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function toggle() {
    setBusy(true);
    setError("");
    try {
      await apiRequest(`/users/${encodeURIComponent(userId)}/follow`, { method: following ? "DELETE" : "POST", token });
      setFollowing(!following);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return <div className="profile-follow"><button className={`button ${following ? "button-soft" : "button-primary"}`} onClick={toggle} disabled={busy}>{busy ? "Updating…" : following ? "Following" : "Follow researcher"}</button>{error && <ErrorBanner message={error} />}</div>;
}

function LibraryPage({ auth }) {
  const [papers, setPapers] = useState([]);
  const [collections, setCollections] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [paperId, setPaperId] = useState("");
  const [collectionName, setCollectionName] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    let active = true;
    setStatus("loading");
    Promise.all([
      apiRequest("/library", { token: auth.token }).then((result) => readList(result, "papers")),
      apiRequest("/library/collections", { token: auth.token }).then((result) => readList(result, "collections")),
    ]).then(([nextPapers, nextCollections]) => {
      if (active) { setPapers(nextPapers); setCollections(nextCollections); setStatus("ready"); setError(""); }
    }).catch((e) => { if (active) { setError(errorMessage(e)); setStatus("error"); } });
    return () => { active = false; };
  }, [auth.token, refresh]);
  async function savePaper(event) {
    event.preventDefault();
    if (!paperId.trim()) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await apiRequest("/library/save", { method: "POST", token: auth.token, body: { paper_id: paperId.trim() } });
      setPaperId("");
      setNotice("Paper saved to your library.");
      setRefresh((n) => n + 1);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function removePaper(id) {
    setBusy(true);
    setError("");
    try {
      await apiRequest(`/library/${encodeURIComponent(id)}`, { method: "DELETE", token: auth.token });
      setPapers((current) => current.filter((paper) => String(recordId(paper)) !== String(id)));
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function createCollection(event) {
    event.preventDefault();
    if (!collectionName.trim()) return;
    setBusy(true);
    setError("");
    try {
      await apiRequest("/library/collections", { method: "POST", token: auth.token, body: { name: collectionName.trim() } });
      setCollectionName("");
      setNotice("Collection created.");
      setRefresh((n) => n + 1);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return (
    <>
      <PageHeading kicker="A PERSONAL RESEARCH SHELF" title={<>Keep the things<br /><em>worth returning to.</em></>} description="Your saved papers and collections, gathered in one place." />
      {error && <ErrorBanner message={error} />}
      {notice && <div className="success-banner"><span className="status-dot" />{notice}<button onClick={() => setNotice("")} aria-label="Dismiss">×</button></div>}
      <section className="library-tools">
        <form className="add-paper-form" onSubmit={savePaper}>
          <div className="tool-icon"><Icon name="bookmark" size={19} /></div>
          <div className="tool-copy"><strong>Save a paper</strong><span>Add by the paper ID provided by the research library.</span></div>
          <input value={paperId} onChange={(e) => setPaperId(e.target.value)} aria-label="Paper ID" placeholder="Enter paper ID…" />
          <button className="button button-primary" disabled={busy || !paperId.trim()}><Icon name="plus" size={16} /> Save paper</button>
        </form>
        <form className="add-collection-form" onSubmit={createCollection}>
          <div className="tool-icon tool-icon-soft"><Icon name="book" size={19} /></div>
          <div className="tool-copy"><strong>Start a collection</strong><span>Group research around a question or project.</span></div>
          <input value={collectionName} onChange={(e) => setCollectionName(e.target.value)} aria-label="Collection name" placeholder="Name your collection…" />
          <button className="button button-outline" disabled={busy || !collectionName.trim()}><Icon name="plus" size={16} /> Create</button>
        </form>
      </section>
      {status === "loading" && <LoadingCard label="Opening your library…" />}
      {status === "error" && <ErrorPanel message={error} onRetry={() => setRefresh((n) => n + 1)} />}
      {status === "ready" && (
        <>
          <section className="library-section">
            <div className="section-title-row"><div><p className="eyebrow">YOUR READING LIST</p><h2>Saved papers <span className="title-count">{papers.length}</span></h2></div><span className="member-count">PRIVATE TO YOU</span></div>
            {papers.length === 0 ? <EmptyPanel icon="book" title="A good read belongs on your shelf." body="Save a paper using its library ID to keep it close. The list will fill as your library grows." /> : (
              <div className="paper-list">{papers.map((paper, index) => {
                const id = recordId(paper);
                const title = paper.title || paper.paper_title || "Untitled paper";
                return <article className="paper-row" key={id ?? index}><div className="paper-cover"><Icon name="book" size={22} /><span>RESEARCH<br />PAPER</span></div><div className="paper-info"><h3>{title}</h3><p>{paper.authors || paper.author || "Authors not listed"}{paper.year ? ` · ${paper.year}` : ""}</p><span className="paper-source">{paper.source || paper.journal || paper.doi || "Saved to Commons"}</span></div><button className="remove-button" disabled={busy || !id} onClick={() => removePaper(id)}>Remove</button></article>;
              })}</div>
            )}
          </section>
          <section className="library-section">
            <div className="section-title-row"><div><p className="eyebrow">THOUGHTFULLY ORGANIZED</p><h2>Your collections <span className="title-count">{collections.length}</span></h2></div></div>
            {collections.length === 0 ? <EmptyPanel icon="bookmark" title="Collections make connections." body="Create a collection above to start gathering work around a shared theme." /> : <div className="collection-grid">{collections.map((collection, index) => <article className="collection-card" key={recordId(collection) ?? index}><div className="collection-art"><Icon name="book" size={23} /><span>FIELD NOTES</span></div><h3>{collection.name || collection.title || "Untitled collection"}</h3><p>{collection.description || "A collection for your research journey."}</p><span className="collection-count">{collection.paper_count ?? collection.items_count ?? 0} PAPERS</span></article>)}</div>}
          </section>
          <div className="pending-contract"><Icon name="spark" size={17} /><span>Private notes and adding papers to collections need API routes that are not in the current project contract. This UI is ready to be extended when those routes are agreed.</span></div>
        </>
      )}
    </>
  );
}

function Avatar({ name = "Researcher", initials, size = "regular" }) {
  const letters = initials || String(name).split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  return <span className={`avatar avatar-${size}`} aria-label={name}>{letters || "R"}</span>;
}

function EmptyPanel({ icon, title, body }) {
  return <div className="empty-panel"><div className="empty-icon"><Icon name={icon} size={21} /></div><h3>{title}</h3><p>{body}</p></div>;
}

function LoadingCard({ label }) {
  return <div className="loading-card"><span className="spinner" />{label}</div>;
}

function LoadingPage() {
  return <main className="full-loading"><span className="brand-mark"><span /></span><span>Making space for your work…</span></main>;
}

function ErrorBanner({ message }) {
  return <div className="error-banner" role="alert"><span>!</span>{message}</div>;
}

function ErrorPanel({ message, onRetry }) {
  return <div className="error-panel"><div className="error-symbol">!</div><h3>We couldn’t load this right now.</h3><p>{message}</p>{onRetry && <button className="button button-outline" onClick={onRetry}>Try again</button>}</div>;
}

function NotFoundPage() {
  return <main className="not-found"><Link to="/feed" className="brand"><span className="brand-mark"><span /></span><span>commons<span className="brand-period">.</span></span></Link><p className="eyebrow">404 · WRONG TURN</p><h1>This page is still<br /><em>being researched.</em></h1><Link to="/feed" className="button button-primary">Back to the Commons <Icon name="arrow" size={16} /></Link></main>;
}

function formatDate(value) {
  if (!value) return "Recently";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(date);
}

export default App;

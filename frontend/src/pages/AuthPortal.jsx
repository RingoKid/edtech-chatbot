import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Sparkles, TimerReset, Users2, Zap } from "lucide-react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import useAuth from "../hooks/useAuth";

const highlightCards = [
  {
    title: "Teacher-first onboarding",
    body: "Invite grade-level teams in one click so every classroom keeps the same guardrails.",
    accent: "from-primary-500/10 to-secondary-500/20",
  },
  {
    title: "Session continuity",
    body: "Access drafts, rubrics, and tutoring transcripts from any device with automatic session recovery.",
    accent: "from-accent-500/10 to-primary-500/5",
  },
];

const timeline = [
  {
    id: "01",
    title: "Secure login",
    detail: "Use your school email to unlock educator-specific journeys.",
    icon: ShieldCheck,
    color: "text-primary-600",
  },
  {
    id: "02",
    title: "Session is minted",
    detail:
      "We issue a short-lived classroom token plus a rotating refresh ticket.",
    icon: TimerReset,
    color: "text-secondary-600",
  },
  {
    id: "03",
    title: "Continue teaching",
    detail:
      "Jump back into prompts, parameter sets, or student feedback exactly where you paused.",
    icon: Zap,
    color: "text-accent-600",
  },
];

const roleOptions = [
  { value: "USER", label: "Teacher / Coach" },
  { value: "ADMIN", label: "Program Admin" },
];

const initialForm = {
  fullName: "",
  email: "",
  password: "",
  role: roleOptions[0].value,
};

const initialStatus = { type: "idle", message: "" };

const AuthPortal = ({ defaultMode = "login" }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, login, signup } = useAuth();
  const [mode, setMode] = useState(defaultMode);
  const redirectPath = location.state?.from || "/ai-teaching-assistant";

  const [formData, setFormData] = useState(() => ({ ...initialForm }));
  const [status, setStatus] = useState(initialStatus);
  const [pending, setPending] = useState(false);
  const [keepSignedIn, setKeepSignedIn] = useState(true);

  useEffect(() => {
    setMode(defaultMode);
    setStatus(initialStatus);
    setFormData({ ...initialForm });
    setKeepSignedIn(true);
  }, [defaultMode]);

  useEffect(() => {
    if (!user) {
      return;
    }
    setStatus({
      type: "success",
      message: `You're signed in as ${user.full_name ?? user.email}`,
    });
  }, [user]);

  const isSignup = mode === "signup";

  const headline = useMemo(
    () =>
      isSignup
        ? "Create your educator workspace"
        : "Welcome back, keep the lesson momentum going",
    [isSignup]
  );

  const subcopy = useMemo(
    () =>
      isSignup
        ? "Personalize onboarding for your grade band, then invite collaborators once your account is live."
        : "Pick up the exact conversation thread, rubric template, or student conference you paused earlier today.",
    [isSignup]
  );

  const handleChange = (evt) => {
    const { name, value } = evt.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setPending(true);
    setStatus({
      type: "info",
      message: isSignup
        ? "Creating your educator workspace..."
        : "Securing your session...",
    });

    try {
      if (isSignup) {
        await signup({
          fullName: formData.fullName.trim(),
          email: formData.email.trim(),
          password: formData.password,
          role: formData.role,
          remember: true,
        });
      } else {
        await login({
          email: formData.email.trim(),
          password: formData.password,
          remember: keepSignedIn,
        });
      }

      setStatus({
        type: "success",
        message: "Redirecting you to the teaching workspace...",
      });
      navigate(redirectPath, { replace: true });
    } catch (error) {
      setStatus({
        type: "error",
        message: error?.message || "Unable to authenticate. Please try again.",
      });
    } finally {
      setPending(false);
    }
  };

  const resetStatus = () => setStatus(initialStatus);

  return (
    <section className="min-h-screen w-full bg-gradient-to-b from-white via-primary-50/40 to-secondary-50/60 pt-28 pb-16">
      <div className="container">
        <div className="flex flex-col gap-4 text-center mb-12">
          <span className="inline-flex items-center justify-center rounded-full bg-white/60 px-4 py-1 text-xs font-semibold tracking-widest text-primary-700 uppercase">
            Secure Workspace Access
          </span>
          <h1 className="text-3xl md:text-5xl font-extrabold font-display text-gray-900 leading-tight">
            Sign in once, guide students all day
          </h1>
          <p className="text-base md:text-lg text-gray-600 max-w-3xl mx-auto">
            Keeping classroom data private while making it effortless for
            instructors to resume teaching.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] items-stretch">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="card relative overflow-hidden p-8 bg-white shadow-2xl"
          >
            <div
              className="absolute inset-0 pointer-events-none opacity-70"
              aria-hidden="true"
            >
              <div className="absolute -top-10 -right-16 h-48 w-48 rounded-full bg-primary-200 blur-3xl" />
              <div className="absolute bottom-0 left-4 h-40 w-40 rounded-full bg-secondary-200 blur-3xl" />
            </div>

            <div className="relative z-10 space-y-8">
              <div>
                <p className="text-sm font-semibold uppercase text-primary-600 tracking-[0.2em]">
                  Designed for Teachers
                </p>
                <h2 className="mt-3 text-2xl md:text-3xl font-display font-bold text-gray-900">
                  {headline}
                </h2>
                <p className="mt-2 text-gray-600">{subcopy}</p>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {highlightCards.map((card) => (
                  <div
                    key={card.title}
                    className={`rounded-2xl border border-white/60 bg-gradient-to-br ${card.accent} px-5 py-4 shadow-inner`}
                  >
                    <p className="text-sm font-semibold text-gray-900">
                      {card.title}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">{card.body}</p>
                  </div>
                ))}
              </div>

              <div className="space-y-4">
                {timeline.map((step) => (
                  <div key={step.id} className="flex gap-4 items-start">
                    <div className="flex-shrink-0 rounded-full bg-gray-900/5 size-12 flex items-center justify-center">
                      <step.icon className={`size-5 ${step.color}`} />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-gray-500">
                        Step {step.id}
                      </p>
                      <p className="font-semibold text-gray-900">
                        {step.title}
                      </p>
                      <p className="text-sm text-gray-600">{step.detail}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl bg-gray-900 text-white p-5 flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <Users2 className="size-5 text-secondary-200" />
                  <p className="text-sm font-semibold tracking-wide uppercase">
                    Staff collaboration
                  </p>
                </div>
                <p className="text-lg font-semibold">
                  Share guardrails, prompts, and lesson starters without leaving
                  the workspace.
                </p>
                <p className="text-sm text-gray-300">
                  When we ship the session overview, you'll see live classroom
                  activity here. No extra dashboards required.
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="card border-primary-100 bg-white/95 shadow-2xl"
          >
            <div className="p-8">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-xs uppercase font-semibold tracking-[0.3em] text-primary-600">
                    Access Portal
                  </p>
                  <h3 className="text-2xl font-display font-bold text-gray-900">
                    {isSignup ? "Create account" : "Sign in"}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {isSignup
                      ? "No credit card required. Invite teammates after onboarding."
                      : "Use your school email to rejoin your sessions."}
                  </p>
                </div>
                <Sparkles className="size-8 text-primary-500" />
              </div>

              {user && (
                <div className="mt-6 rounded-2xl border border-primary-100 bg-primary-50/60 p-4 text-left">
                  <p className="text-sm font-semibold text-primary-800">
                    You're signed in as {user.full_name || user.email}.
                  </p>
                  <p className="text-xs text-primary-600">
                    Jump straight into your saved prompts or continue with
                    another account below.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-3">
                    <Link
                      to={redirectPath}
                      className="inline-flex items-center rounded-xl bg-white px-4 py-2 text-sm font-semibold text-primary-700 shadow"
                    >
                      Go to workspace
                    </Link>
                  </div>
                </div>
              )}

              <div className="mt-6 grid grid-cols-2 rounded-full bg-gray-100 p-1 text-sm font-medium">
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    resetStatus();
                  }}
                  className={`rounded-full px-4 py-2 transition-all ${
                    !isSignup
                      ? "bg-white text-gray-900 shadow"
                      : "text-gray-500"
                  }`}
                >
                  Sign in
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMode("signup");
                    resetStatus();
                  }}
                  className={`rounded-full px-4 py-2 transition-all ${
                    isSignup ? "bg-white text-gray-900 shadow" : "text-gray-500"
                  }`}
                >
                  Create account
                </button>
              </div>

              <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
                {isSignup && (
                  <div className="space-y-2">
                    <label
                      htmlFor="fullName"
                      className="text-sm font-semibold text-gray-700"
                    >
                      Full Name
                    </label>
                    <input
                      id="fullName"
                      name="fullName"
                      type="text"
                      placeholder="Alexis Rivera"
                      className="w-full rounded-2xl border border-gray-200 bg-white/80 px-4 py-3 text-gray-900 shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
                      value={formData.fullName}
                      onChange={handleChange}
                      required
                      disabled={pending}
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <label
                    htmlFor="email"
                    className="text-sm font-semibold text-gray-700"
                  >
                    School Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@district.org"
                    className="w-full rounded-2xl border border-gray-200 bg-white/80 px-4 py-3 text-gray-900 shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    disabled={pending}
                  />
                </div>

                <div className="space-y-2">
                  <label
                    htmlFor="password"
                    className="text-sm font-semibold text-gray-700"
                  >
                    Password
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    placeholder={
                      isSignup ? "Minimum 8 characters" : "Enter your password"
                    }
                    className="w-full rounded-2xl border border-gray-200 bg-white/80 px-4 py-3 text-gray-900 shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    minLength={8}
                    disabled={pending}
                  />
                </div>

                {isSignup && (
                  <div className="space-y-2">
                    <label
                      htmlFor="role"
                      className="text-sm font-semibold text-gray-700"
                    >
                      Role
                    </label>
                    <select
                      id="role"
                      name="role"
                      className="w-full rounded-2xl border border-gray-200 bg-white/80 px-4 py-3 text-gray-900 shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
                      value={formData.role}
                      onChange={handleChange}
                      disabled={pending}
                    >
                      {roleOptions.map((role) => (
                        <option key={role.value} value={role.value}>
                          {role.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {!isSignup && (
                  <div className="flex items-center justify-between text-sm">
                    <label
                      htmlFor="rememberMe"
                      className="flex items-center gap-2 text-gray-600"
                    >
                      <input
                        id="rememberMe"
                        type="checkbox"
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        checked={keepSignedIn}
                        onChange={(event) =>
                          setKeepSignedIn(event.target.checked)
                        }
                        disabled={pending}
                      />
                      Keep me signed in
                    </label>
                    <button
                      type="button"
                      className="text-primary-600 font-semibold hover:text-primary-700"
                    >
                      Forgot password?
                    </button>
                  </div>
                )}

                {status.type !== "idle" && (
                  <div
                    className={`rounded-2xl border px-4 py-3 text-sm font-medium ${
                      status.type === "success"
                        ? "border-success-200 bg-success-50 text-success-700"
                        : status.type === "error"
                        ? "border-danger-200 bg-danger-50 text-danger-700"
                        : "border-primary-200 bg-primary-50 text-primary-700"
                    }`}
                  >
                    {status.message}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={pending}
                  className="w-full rounded-2xl bg-gradient-to-r from-primary-600 via-secondary-600 to-primary-700 px-4 py-3 text-white font-semibold shadow-lg transition-all hover:shadow-xl disabled:opacity-70"
                >
                  {pending
                    ? "Preparing..."
                    : isSignup
                    ? "Create account"
                    : "Sign in"}
                </button>

                <p className="text-xs text-gray-500 text-center">
                  {isSignup
                    ? "By continuing you accept our privacy-first data policy for students."
                    : "Single sign-on & district-specific tiles arrive soon."}
                </p>
              </form>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default AuthPortal;

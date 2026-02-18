import { useMemo, useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Menu,
  X,
  BookOpen,
  ChevronDown,
  LogOut,
  UserRound,
} from "lucide-react";
import { cn } from "../utils/cn";
import useAuth from "../hooks/useAuth";

const Navigation = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    setAccountOpen(false);
    setIsOpen(false);
  }, [location.pathname]);

  const userInitials = useMemo(() => {
    if (!user) return "";
    const base = user.full_name || user.email || "Educator";
    const parts = base.split(" ");
    const letters = parts
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase());
    return letters.join("") || base[0]?.toUpperCase();
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const navItems = [
    { name: "Homepage", href: "/" },
    {
      name: "Best Practices Modeled",
      href: "/best-practices",
      dropdown: [
        { name: "Idea Generation & Organization", href: "/idea-generation" },
        { name: "Language Construction", href: "/vocabulary-syntax" },
        { name: "Transcription", href: "/handwriting-spelling" },
      ],
    },
    { name: "AI Teaching Assistant", href: "/ai-teaching-assistant" },
  ];

  const isHomePage = location.pathname === "/";

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled || !isHomePage
          ? "bg-white/95 backdrop-blur-lg shadow-lg border-b border-gray-200/50"
          : "bg-transparent"
      )}
    >
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
            <Link to="/" className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-lg">
                <BookOpen className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <span className="text-base sm:text-lg lg:text-xl font-bold font-display gradient-text leading-tight">
                <span className="hidden sm:inline">Language For Composing</span>
                <span className="sm:hidden">LFC</span>
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4 lg:space-x-8">
            {navItems.map((item, index) => (
              <motion.div
                key={item.name}
                className="relative group"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                {item.dropdown ? (
                  <div className="relative">
                    <Link
                      to={item.href}
                      className={cn(
                        "relative px-4 py-2 text-sm font-medium transition-colors duration-200 rounded-lg whitespace-nowrap flex items-center gap-1",
                        location.pathname === item.href ||
                          item.dropdown.some(
                            (sub) => location.pathname === sub.href
                          )
                          ? "bg-primary-100 text-primary-700"
                          : scrolled || !isHomePage
                          ? "text-gray-900 hover:text-primary-600 hover:bg-primary-50"
                          : "text-white hover:text-primary-200 hover:bg-white/10"
                      )}
                    >
                      {item.name}
                      <ChevronDown className="w-4 h-4 transition-transform duration-200 group-hover:rotate-180" />
                      {(location.pathname === item.href ||
                        item.dropdown.some(
                          (sub) => location.pathname === sub.href
                        )) && (
                        <motion.div
                          className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-secondary-500"
                          layoutId="activeTab"
                        />
                      )}
                    </Link>

                    {/* Dropdown */}
                    <AnimatePresence>
                      <motion.div
                        className="absolute top-full left-0 mt-2 w-64 bg-white border border-gray-200 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50"
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="py-2">
                          {item.dropdown.map((subItem, subIndex) => (
                            <motion.div
                              key={subItem.name}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: subIndex * 0.05 }}
                            >
                              <Link
                                to={subItem.href}
                                className={cn(
                                  "block px-4 py-3 text-sm font-medium transition-colors duration-200 hover:bg-primary-50 hover:text-primary-600",
                                  location.pathname === subItem.href
                                    ? "bg-primary-100 text-primary-700 border-r-2 border-primary-500"
                                    : "text-gray-700"
                                )}
                              >
                                {subItem.name}
                              </Link>
                            </motion.div>
                          ))}
                        </div>
                      </motion.div>
                    </AnimatePresence>
                  </div>
                ) : (
                  <Link
                    to={item.href}
                    className={cn(
                      "relative px-4 py-2 text-sm font-medium transition-colors duration-200 rounded-lg whitespace-nowrap",
                      location.pathname === item.href
                        ? "bg-primary-100 text-primary-700"
                        : scrolled || !isHomePage
                        ? "text-gray-900 hover:text-primary-600 hover:bg-primary-50"
                        : "text-white hover:text-primary-200 hover:bg-white/10"
                    )}
                  >
                    {item.name}
                    {location.pathname === item.href && (
                      <motion.div
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-secondary-500"
                        layoutId="activeTab"
                      />
                    )}
                  </Link>
                )}
              </motion.div>
            ))}
            <div className="flex items-center gap-3 pl-4 border-l border-gray-200/60">
              {isAuthenticated ? (
                <>
                  <Link
                    to="/ai-teaching-assistant"
                    className="px-4 py-2 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-primary-600 to-secondary-600 shadow-lg hover:shadow-xl transition-all"
                  >
                    Open workspace
                  </Link>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setAccountOpen((prev) => !prev)}
                      className={cn(
                        "flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors",
                        scrolled || !isHomePage
                          ? "border-gray-200 text-gray-900"
                          : "border-white/40 text-white"
                      )}
                    >
                      <div className="w-8 h-8 rounded-full bg-gray-900 text-white flex items-center justify-center text-xs">
                        {userInitials}
                      </div>
                      <ChevronDown
                        className={cn(
                          "w-4 h-4 transition-transform",
                          accountOpen ? "rotate-180" : ""
                        )}
                      />
                    </button>
                    <AnimatePresence>
                      {accountOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ duration: 0.2 }}
                          className="absolute right-0 mt-3 w-72 rounded-2xl bg-white shadow-2xl border border-gray-100"
                        >
                          <div className="p-4 space-y-1 border-b border-gray-100">
                            <p className="text-sm font-semibold text-gray-900">
                              {user?.full_name || "Logged in"}
                            </p>
                            <p className="text-xs text-gray-500 truncate">
                              {user?.email}
                            </p>
                          </div>
                          <div className="p-3 space-y-2">
                            <Link
                              to="/ai-teaching-assistant"
                              className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-primary-700 bg-primary-50"
                            >
                              <UserRound className="w-4 h-4" />
                              View workspace
                            </Link>
                            <button
                              type="button"
                              onClick={handleLogout}
                              className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-danger-700 hover:bg-danger-50"
                            >
                              <LogOut className="w-4 h-4" />
                              Sign out
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-semibold transition-colors duration-200",
                      scrolled || !isHomePage
                        ? "text-gray-900 hover:text-primary-700 hover:bg-primary-50"
                        : "text-white/80 hover:text-white hover:bg-white/10"
                    )}
                  >
                    Sign in
                  </Link>
                  <Link
                    to="/signup"
                    className="inline-flex items-center rounded-xl bg-gradient-to-r from-primary-600 to-secondary-600 px-4 py-2 text-sm font-semibold text-white shadow-lg hover:shadow-xl transition-all"
                  >
                    Create account
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <motion.button
            className="md:hidden p-2 rounded-lg flex-shrink-0"
            onClick={() => setIsOpen(!isOpen)}
            whileTap={{ scale: 0.95 }}
          >
            <AnimatePresence mode="wait">
              {isOpen ? (
                <motion.div
                  key="close"
                  initial={{ rotate: -90 }}
                  animate={{ rotate: 0 }}
                  exit={{ rotate: 90 }}
                  transition={{ duration: 0.2 }}
                >
                  <X
                    className={cn(
                      "w-6 h-6",
                      scrolled || !isHomePage ? "text-gray-900" : "text-white"
                    )}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="menu"
                  initial={{ rotate: 90 }}
                  animate={{ rotate: 0 }}
                  exit={{ rotate: -90 }}
                  transition={{ duration: 0.2 }}
                >
                  <Menu
                    className={cn(
                      "w-6 h-6",
                      scrolled || !isHomePage ? "text-gray-900" : "text-white"
                    )}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.button>
        </div>

        {/* Mobile Navigation */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="md:hidden bg-white border-t border-gray-200 shadow-lg"
            >
              <div className="py-4 space-y-2">
                {navItems.map((item, index) => (
                  <motion.div
                    key={item.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Link
                      to={item.href}
                      className={cn(
                        "block px-4 py-3 font-medium transition-colors duration-200 rounded-lg mx-2",
                        location.pathname === item.href
                          ? "bg-primary-100 text-primary-700"
                          : "text-gray-900 hover:bg-gray-50 hover:text-primary-600"
                      )}
                      onClick={() => setIsOpen(false)}
                    >
                      {item.name}
                    </Link>
                  </motion.div>
                ))}
                <div className="px-4 pt-4 border-t border-gray-100 space-y-3">
                  {isAuthenticated ? (
                    <>
                      <div className="rounded-2xl border border-gray-200 p-4">
                        <p className="text-sm font-semibold text-gray-900">
                          {user?.full_name || "Logged in"}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {user?.email}
                        </p>
                      </div>
                      <Link
                        to="/ai-teaching-assistant"
                        className="block w-full rounded-xl bg-gradient-to-r from-primary-600 to-secondary-600 px-4 py-3 text-center font-semibold text-white shadow-lg"
                        onClick={() => setIsOpen(false)}
                      >
                        Open workspace
                      </Link>
                      <button
                        type="button"
                        onClick={handleLogout}
                        className="w-full rounded-xl border border-gray-200 px-4 py-3 text-center font-semibold text-gray-900"
                      >
                        Sign out
                      </button>
                    </>
                  ) : (
                    <>
                      <Link
                        to="/login"
                        className="block w-full rounded-xl border border-gray-200 px-4 py-3 text-center font-semibold text-gray-900"
                        onClick={() => setIsOpen(false)}
                      >
                        Sign in
                      </Link>
                      <Link
                        to="/signup"
                        className="block w-full rounded-xl bg-gradient-to-r from-primary-600 to-secondary-600 px-4 py-3 text-center font-semibold text-white shadow-lg"
                        onClick={() => setIsOpen(false)}
                      >
                        Create account
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
};

export default Navigation;

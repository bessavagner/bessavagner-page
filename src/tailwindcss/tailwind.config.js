/** @type {import("tailwindcss").Config} */
const plugin = require("tailwindcss/plugin");

module.exports = {
  content: [
    "../../*.py",
    "../app/*.py",
    "../app/**/*.py",
    "../static/css/*.css",
    "../static/js/*.js",
    "../static/js/**/*.js",
    "../templates/*.html",
    "../templates/**/*.html",
  ],
  theme: {
    extend: {
      fontSize: {
        md: "1.0rem",
        xsm: "0.75rem",
        xxsm: "0.625rem",
      },
      textShadow: {
        sm: "0 1px 2px var(--tw-shadow-color)",
        DEFAULT: "0 2px 4px var(--tw-shadow-color)",
        lg: "0 8px 16px var(--tw-shadow-color)",
      },
      boxShadow: {
        "3xl": "0 10px 15px 10px rgba(0, 0, 0, 0.3)",
        "inner-xl": "inset 0px -5px 10px 5px rgba(0, 0, 0, 0.3)",
      },
      animation: {
        'fade-in': 'fadeIn 2s ease-in-out',
        'slide-in': 'slideIn 1s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        slideIn: {
          '0%': { transform: 'translateY(100%)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        },
      },
    },
  },
  daisyui: {
    themes: [
      {
        custom: {
          "primary": "#3a3d98",
          "primary-content": "#d3d7ec",
          "secondary": "#727d95",
          "secondary-content": "#040508",
          "accent": "#daa520",
          "accent-content": "#110a00",
          "neutral": "#2f2f2f",
          "neutral-content": "#d1d1d1",
          "base-100": "#f7fafc",
          "base-200": "#d7d9db",
          "base-300": "#b7babb",
          "base-content": "#151516",
          "info": "#4c88d2",
          "info-content": "#020610",
          "success": "#3aab5f",
          "success-content": "#010b03",
          "warning": "#eba417",
          "warning-content": "#130a00",
          "error": "#d9534f",
          "error-content": "#110202",
        },
        "custom-dark": {
          "primary": "#1d2342",
          "primary-content": "#ccced7",
          "secondary": "#444c63",
          "secondary-content": "#d6d9de",
          "accent": "#b8860b",
          "accent-content": "#0c0600",
          "neutral": "#1b1e28",
          "neutral-content": "#cccdcf",
          "base-100": "#121621",
          "base-200": "#0e121b",
          "base-300": "#0a0d16",
          "base-content": "#c9cace",
          "info": "#3b82fc",
          "info-content": "#010616",
          "success": "#28a745",
          "success-content": "#010a02",
          "warning": "#ffc107",
          "warning-content": "#160e00",
          "error": "#ff4d4f",
          "error-content": "#160202",
        },
      },
    ],
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/line-clamp"),
    require("@tailwindcss/aspect-ratio"),
    require("daisyui"),
    plugin(function ({ matchUtilities, theme }) {
      matchUtilities(
        {
          "text-shadow": (value) => ({
            textShadow: value,
          }),
        },
        { values: theme("textShadow") }
      );
    }),
  ],
};

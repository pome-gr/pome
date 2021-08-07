module.exports = {
  purge: {
    enabled: process.env.PURGE_CSS_ENABLED === "true" ?? false,
    content: ["./pome/templates/**/*.html"],
  },
};
